from decimal import Decimal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView


SATOSHI_WEIGHT = 1000000000


def satoshi2bst(amount):
    return Decimal(str(amount)) / SATOSHI_WEIGHT


def get_main_window():
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QWebEngineView):
            return widget
    return None
