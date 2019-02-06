import os
import pathlib
import sys
from decimal import Decimal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView


SATOSHI_WEIGHT = 100000000


def satoshi2bst(amount):
    return Decimal(str(amount)) / SATOSHI_WEIGHT


def get_data_dir():
    if getattr(sys, 'frozen', None):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            # pyinstaller app
            return meipass

        # py2app binary
        return os.path.realpath(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        )

    return os.path.dirname(os.path.abspath(__file__))


def get_templates_dir_path():
    return os.path.join(get_data_dir(), 'templates')


def get_media_dir_path():
    return os.path.join(get_data_dir(), 'media')


def get_hprox_dir_path():
    home = str(pathlib.Path.home())

    hprox_dir = os.path.join(home, '.hproxy')
    if not os.path.exists(hprox_dir):
        os.mkdir(hprox_dir)

    return hprox_dir


def get_db_file_path():
    return os.path.join(get_hprox_dir_path(), 'db.sqlite3')



def get_main_window():
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QWebEngineView):
            return widget
    return None
