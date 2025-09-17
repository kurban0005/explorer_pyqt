import fnmatch
import logging
import os
import platform
import subprocess
from typing import Optional

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QDir, QThread, pyqtSignal, QModelIndex
from PyQt5.QtWidgets import QFileSystemModel, QInputDialog

from qt_design import Ui_MainWindow

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('explorer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FileExplorer')


class FileSearchThread(QThread):
    """Поток для поиска файлов по заданному шаблону."""

    found_file = pyqtSignal(str)
    search_finished = pyqtSignal()

    def __init__(self, root_path: str, pattern: str) -> None:
        """
        Инициализация потока поиска.

        Args:
            root_path: Корневой путь для поиска
            pattern: Шаблон для поиска файлов
        """
        super().__init__()
        self.root_path = root_path
        self.pattern = pattern
        self._is_running = True

    def run(self) -> None:
        """Основной метод выполнения поиска."""
        try:
            logger.info(f'Starting search for pattern: {self.pattern}')
            for root, dirs, files in os.walk(self.root_path):
                if not self._is_running:
                    break

                for file in files:
                    if not self._is_running:
                        break

                    if fnmatch.fnmatch(file.lower(), f'*{self.pattern.lower()}*'):
                        file_path = os.path.join(root, file)
                        self.found_file.emit(file_path)
        except Exception as e:
            logger.error(f'Search error: {e}')
        finally:
            logger.info('Search finished')
            self.search_finished.emit()

    def stop(self) -> None:
        """Остановка выполнения поиска."""
        logger.info('Stopping search thread')
        self._is_running = False


class FileExplorer(QtWidgets.QMainWindow):
    """Главный класс файлового менеджера с графическим интерфейсом."""

    def __init__(self) -> None:
        """Инициализация главного окна приложения."""
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())
        logger.info('Application started')

        # Улучшенные стили для лучшей читаемости на macOS
        if platform.system() == 'Darwin':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: rgb(0, 40, 20);
                    font-family: 'SF Pro Text', 'Helvetica Neue', sans-serif;
                }
                QLineEdit {
                    color: rgb(255, 255, 255);
                    font-size: 13px;
                    padding: 5px;
                    border: 1px solid rgb(100, 100, 100);
                    border-radius: 4px;
                }
                QPushButton {
                    color: white;
                    font-size: 12px;
                    padding: 4px;
                    border-radius: 4px;
                }
                QTreeView {
                    background-color: rgb(240, 240, 240);
                    alternate-background-color: rgb(230, 230, 230);
                    font-size: 12px;
                }
                QLabel {
                    color: rgb(0, 120, 0);
                    font-size: 11px;
                }
            """)

        # Настройка модели файловой системы
        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser('~'))
        self.model.setFilter(QDir.AllEntries | QDir.AllDirs | QDir.NoDotAndDotDot)

        # Устанавливаем модель в QTreeView
        self.ui.file_tree.setModel(self.model)
        self.ui.file_tree.setRootIndex(self.model.index(os.path.expanduser('~')))
        self.ui.file_tree.setColumnWidth(0, 250)

        # Переменная для отслеживания скрытых файлов
        self.show_hidden = False

        # Обработчики событий
        self.ui.file_tree.clicked.connect(self.on_tree_click)
        self.ui.btn_open.clicked.connect(self.open_file)
        self.ui.btn_root_reset.clicked.connect(self.change_root_reset)
        self.ui.btn_root_next.clicked.connect(self.change_root_next)
        self.ui.btn_root_up.clicked.connect(self.change_root_up)
        self.ui.btn_root_home.clicked.connect(self.change_root_home)
        self.ui.btn_toggle_hidden.clicked.connect(self.toggle_hidden_files)
        self.ui.btn_search.clicked.connect(self.search_files)

        # Поток для поиска файлов
        self.search_thread: Optional[FileSearchThread] = None

        self.update_status('Готов')

    def on_tree_click(self, index: QModelIndex) -> None:
        """
        Обработчик клика по элементу дерева файлов.

        Args:
            index: Индекс выбранного элемента
        """
        path = self.model.filePath(index)
        self.ui.path.setText(path)
        self.update_status(f'Выбран: {path}')
        logger.info(f'Selected: {path}')

    def open_file(self) -> None:
        """Открытие выбранного файла или директории."""
        path = self.ui.path.text()
        if not path:
            self.update_status('Путь не указан!')
            logger.warning('No path specified')
            return

        if os.path.exists(path):
            try:
                if platform.system() == 'Windows':
                    os.startfile(path)
                elif platform.system() == 'Darwin':
                    subprocess.call(['open', path])
                else:
                    subprocess.call(['xdg-open', path])

                if os.path.isdir(path):
                    self.update_status(f'Открыт каталог: {path}')
                    logger.info(f'Opened directory: {path}')
                else:
                    self.update_status(f'Открыт файл: {path}')
                    logger.info(f'Opened file: {path}')
            except Exception as e:
                error_msg = f'Ошибка при открытии: {str(e)}'
                self.update_status(error_msg)
                logger.error(error_msg)
        else:
            error_msg = 'Указанный путь не существует!'
            self.update_status(error_msg)
            logger.error(error_msg)

    def update_status(self, message: str) -> None:
        """
        Обновление текста статусной строки.

        Args:
            message: Текст для отображения
        """
        self.ui.status.setText(message)

    def change_root(self, path: str) -> bool:
        """
        Изменение корневой директории файловой модели.

        Args:
            path: Новый корневой путь
        """
        self.model.setRootPath(path)
        self.ui.file_tree.setRootIndex(self.model.index(path))

    def change_root_reset(self):
        '''Сбрасывает корневую директорию в состояние "по умолчанию".'''
        path = os.path.expanduser("")
        # Сброс дерева и возвращение к исходному корню
        self.change_root(path)
        self.update_status("Вы вернулись в корневой каталог.")


    def change_root_up(self) -> None:
        """Переход на уровень выше в файловой иерархии."""
        current_index = self.ui.file_tree.rootIndex()
        current_path = self.model.filePath(current_index)
        parent_path = os.path.dirname(current_path)

        if parent_path and self.change_root(parent_path):
            self.ui.path.setText(parent_path)
            self.update_status(f'Вы перешли в: {parent_path}')
            logger.info(f'Moved up to: {parent_path}')
        else:
            error_msg = 'Невозможно перейти в директорию выше!'
            self.update_status(error_msg)
            logger.error(error_msg)

    def change_root_home(self) -> None:
        """Переход в домашнюю директорию пользователя."""
        path = os.path.expanduser('~')
        if self.change_root(path):
            self.ui.path.setText('')
            self.update_status('Вы перешли в домашний каталог.')
            logger.info('Changed to home directory')

    def change_root_next(self) -> None:
        """Переход в директорию, указанную в поле пути."""
        path = self.ui.path.text()
        path = self.ui.path.text()
        self.change_root(path)
        self.update_status(f"Вы перешли в: {path}")
        logger.info(f'Changed to directory: {path}')


    def toggle_hidden_files(self) -> None:
        """Переключение отображения скрытых файлов."""
        self.show_hidden = not self.show_hidden

        if self.show_hidden:
            self.model.setFilter(self.model.filter() | QDir.Hidden)
            self.update_status('Показаны скрытые файлы')
            logger.info('Showing hidden files')
        else:
            self.model.setFilter(self.model.filter() & ~QDir.Hidden)
            self.update_status('Скрытые файлы скрыты')
            logger.info('Hiding hidden files')

    def search_files(self) -> None:
        """Инициализация поиска файлов по шаблону."""
        search_text, ok = QInputDialog.getText(self, 'Поиск файлов', 'Введите имя файла:')
        if ok and search_text:
            # Останавливаем предыдущий поиск, если он активен
            if self.search_thread and self.search_thread.isRunning():
                self.search_thread.stop()
                self.search_thread.wait()

            self.update_status(f'Поиск: {search_text}...')
            logger.info(f'Starting search for: {search_text}')

            # Создаем и запускаем поток поиска
            self.search_thread = FileSearchThread(self.model.rootPath(), search_text)
            self.search_thread.found_file.connect(self.on_file_found)
            self.search_thread.search_finished.connect(self.on_search_finished)
            self.search_thread.start()

    def on_file_found(self, file_path: str) -> None:
        """
        Обработчик найденного файла.

        Args:
            file_path: Путь к найденному файлу
        """
        parent_dir = os.path.dirname(file_path)
        if self.change_root(parent_dir):
            index = self.model.index(file_path)
            self.ui.file_tree.setCurrentIndex(index)
            self.ui.path.setText(file_path)
            self.update_status(f'Найден: {file_path}')
            logger.info(f'Found file: {file_path}')

    def on_search_finished(self) -> None:
        """Обработчик завершения поиска."""
        self.update_status('Поиск завершен')
        logger.info('Search completed')

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Обработчик события закрытия приложения.

        Args:
            event: Событие закрытия
        """
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()
        logger.info('Application closed')
        event.accept()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # Устанавливаем стиль для macOS
    if platform.system() == 'Darwin':
        app.setStyle('Fusion')

    window = FileExplorer()
    window.show()
    sys.exit(app.exec_())
