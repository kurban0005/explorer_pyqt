import platform
import sys
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication

from explorer import FileExplorer


@pytest.fixture(scope="module")
def app_qt():
    """
    Создает и возвращает экземпляр приложения Qt для модульных тестов.
    """
    app = QApplication(sys.argv)
    yield app


@pytest.fixture
def file_explorer(app_qt):
    """
    Создает и возвращает экземпляр FileExplorer для каждого теста.
    """
    explorer = FileExplorer()
    return explorer


def test_open_file_success_directory(file_explorer):
    """
    Тестирует успешное открытие каталога на разных платформах.
    """
    if platform.system() == "Windows":
        with (patch("os.path.exists", return_value=True),
              patch("os.path.isdir", return_value=True),
              patch("os.startfile") as mock_startfile):
            file_explorer.ui.path.setText("/fake/path")
            file_explorer.open_file()
            mock_startfile.assert_called_once_with("/fake/path")
            assert file_explorer.ui.status.text() == "Открыт каталог: /fake/path"
    else:  # Для macOS/Linux
        with (patch("os.path.exists", return_value=True),
              patch("os.path.isdir", return_value=True),
              patch("subprocess.call") as mock_subprocess):
            file_explorer.ui.path.setText("/fake/path")
            file_explorer.open_file()
            mock_subprocess.assert_called_once_with(["open", "/fake/path"])
            assert file_explorer.ui.status.text() == "Открыт каталог: /fake/path"


def test_open_file_success_file(file_explorer):
    """
    Тестирует успешное открытие файла на разных платформах.
    """
    if platform.system() == "Windows":
        with (patch("os.path.exists", return_value=True),
              patch("os.path.isfile", return_value=True),
              patch("os.startfile") as mock_startfile):
            file_explorer.ui.path.setText("/fake/file.txt")
            file_explorer.open_file()
            mock_startfile.assert_called_once_with("/fake/file.txt")
            assert file_explorer.ui.status.text() == "Открыт файл: /fake/file.txt"
    else:  # Для macOS/Linux
        with (patch("os.path.exists", return_value=True),
              patch("os.path.isfile", return_value=True),
              patch("subprocess.call") as mock_subprocess):
            file_explorer.ui.path.setText("/fake/file.txt")
            file_explorer.open_file()
            mock_subprocess.assert_called_once_with(["open", "/fake/file.txt"])
            assert file_explorer.ui.status.text() == "Открыт файл: /fake/file.txt"


def test_open_file_path_not_exist(file_explorer):
    """
    Тестирует открытие несуществующего пути.
    """
    with patch("os.path.exists", return_value=False):
        file_explorer.ui.path.setText("/fake/path")
        file_explorer.open_file()
        assert file_explorer.ui.status.text() == "Указанный путь не существует!"


def test_change_root_reset(file_explorer):
    """
    Тестирует сброс корня в домашний каталог.
    """
    with (patch("os.path.expanduser", return_value="/home/user"),
          patch("explorer.FileExplorer.change_root", return_value=True)):
        file_explorer.change_root_reset()
        assert file_explorer.ui.status.text() == "Вы вернулись в корневой каталог."
        assert file_explorer.ui.path.text() == ""



def test_change_root_up_failure(file_explorer):
    """
    Тестирует неудачный переход в родительский каталог.
    """
    with (patch("os.path.dirname", return_value="/parent/path"),
          patch("os.path.exists", return_value=False)):
        file_explorer.ui.file_tree.setRootIndex(
            file_explorer.model.index("/current/path")
        )
        file_explorer.change_root_up()
        assert file_explorer.ui.status.text() == "Невозможно перейти в директорию выше!"


def test_change_root_home(file_explorer):
    """
    Тестирует переход в домашний каталог.
    """
    with (patch("os.path.expanduser", return_value="/home/user"),
          patch("explorer.FileExplorer.change_root", return_value=True)):
        file_explorer.change_root_home()
        assert file_explorer.ui.path.text() == ""
        assert file_explorer.ui.status.text() == "Вы перешли в домашний каталог."


def test_change_root_next(file_explorer):
    """
    Тестирует переход в указанный каталог.
    """
    with (patch("os.path.exists", return_value=True),
          patch("os.path.isdir", return_value=True)):
        file_explorer.ui.path.setText("/fake/path")
        file_explorer.change_root_next()
        assert file_explorer.ui.path.text() == "/fake/path"
        assert file_explorer.ui.status.text() == "Вы перешли в: /fake/path"


if __name__ == "__main__":
    pytest.main()
