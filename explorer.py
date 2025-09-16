from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileSystemModel
import os
import subprocess
import platform
from qt_design import Ui_MainWindow


class FileExplorer(QtWidgets.QMainWindow):
    '''Класс описывающий проводник и его возможности.'''

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()  # Создаем экземпляр Ui_MainWindow
        self.ui.setupUi(self)  # Настраиваем пользовательский интерфейс
        self.setFixedSize(self.size())

        # Настройка модели файловой системы
        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser(""))  # Устанавливаем корневой путь

        # Устанавливаем модель в QTreeView
        self.ui.file_tree.setModel(self.model)
        self.ui.file_tree.setRootIndex(self.model.index(os.path.expanduser("")))

        # Обработчики событий
        self.ui.file_tree.clicked.connect(self.on_tree_click)  # Обработка клика по элементам дерева
        self.ui.btn_open.clicked.connect(self.open_file)  # Обработка нажатия кнопки выбора папки
        self.ui.btn_root_reset.clicked.connect(self.change_root_reset)
        self.ui.btn_root_next.clicked.connect(self.change_root_next)
        self.ui.btn_root_up.clicked.connect(self.change_root_up)
        self.ui.btn_root_home.clicked.connect(self.change_root_home)
        self.update_status("Готов")  # Устанавливаем начальный статус

    def on_tree_click(self, index):
        '''Выбирает элемент в древе файлов.
        :param index: индекс выбранного элемента в дереве'''
        path = self.model.filePath(index)
        self.ui.path.setText(path)  # Отображаем путь в QLineEdit
        self.update_status(f"Выбран: {path}")  # Обновляем статус

    def open_file(self):
        '''Открывает файл или папку, находящийся по адресу в поле 'path'.'''
        path = self.ui.path.text()  # Получаем текст из QLineEdit
        if os.path.exists(path):  # Проверяем, что путь существует
            if os.path.isdir(path):  # Проверяем, является ли путь директорией
                # Открываем проводник для выбранной директории
                if platform.system() == "Windows":
                    os.startfile(path)  # Открываем в проводнике на Windows
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", path])
                else:  # Linux
                    subprocess.call(["xdg-open", path])
                self.update_status(f"Открыт каталог: {path}")  # Обновляем статус
            elif os.path.isfile(path):  # Проверяем, является ли путь файлом
                # Открываем файл с помощью стандартного приложения
                if platform.system() == "Windows":
                    os.startfile(path)  # Открываем файл на Windows
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", path])
                else:  # Linux
                    subprocess.call(["xdg-open", path])
                self.update_status(f"Открыт файл: {path}")  # Обновляем статус
        else:
            self.update_status("Указанный путь не существует!")  # Если путь не существует

    def update_status(self, message):
        self.ui.status.setText(message)  # Обновляем текст статуса

    def change_root(self, path):
        '''Изменяет корневую директорию в дереве file_tree.
        :param path: путь к каталогу, который надо сделать корневым.'''
        self.model.setRootPath(path)
        self.ui.file_tree.setRootIndex(self.model.index(path))

    def change_root_reset(self):
        '''Сбрасывает корневую директорию в состояние "по умолчанию".'''
        path = os.path.expanduser("")
        # Сброс дерева и возвращение к исходному корню
        self.change_root(path)
        self.update_status("Вы вернулись в корневой каталог.")

    def change_root_up(self):
        '''Переходит в директорию выше и делает её корневой.'''
        current_index = self.ui.file_tree.rootIndex()
        current_path = self.model.filePath(current_index)

        # Получаем родительский путь
        parent_path = os.path.dirname(current_path)

        # Проверяем, существует ли родительская директория
        if parent_path and os.path.exists(parent_path) and os.path.isdir(parent_path):
            self.change_root(parent_path)
            self.ui.path.setText(parent_path)  # Устанавливаем новый корень
            self.update_status(f"Вы перешли в : {parent_path}")
        else:
            self.update_status("Невозможно перейти в директорию выше!")

    def change_root_home(self):
        '''Изменяет корневую директорию на "домашнюю".'''
        path = os.path.expanduser("~")
        self.change_root(path)
        self.update_status("Вы перешли в домашний каталог.")

    def change_root_next(self):
        '''Изменяет корневую директорию на выделенный каталог.'''
        path = self.ui.path.text()
        self.change_root(path)
        self.update_status(f"Вы перешли в : {path}")


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)  # Инициализация приложения
    window = FileExplorer()  # Создаем экземпляр FileExplorer
    window.show()  # Показываем окно
    sys.exit(app.exec_())  # Запускаем приложение
