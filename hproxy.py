import os
import time

import requests
import sys

from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import (QObject, pyqtSlot, QThread, pyqtSignal, QUrl)
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QAction, QApplication, QSystemTrayIcon, QMessageBox, QMenu)

from hpxqt import utils as hpxqt_utils
from hpxqt import db as hpxqt_db
from hpxqt import mng as hpxqt_mng


class Router(QObject):
    """
    Class for connection web, main widgets and network mangers.
    Methods which are called from js file start with 'js_' and
    from Managers start with 'network_' and from main app start with 'app_'.
    """

    init_close = pyqtSignal()

    def __init__(self, window):
        super(Router, self).__init__()
        self.window = window

        self.email = None
        self.password = None
        self.channel = None
        self.TIMEOUT = 10

        self.init_close.connect(self.app_handler_close_connection)

        self.db_manager = hpxqt_db.DatabaseManager()
        self.db_manager.initialize()

    def app_handler_close_connection(self):
        if self.channel:
            self.channel.close_connections()

    def app_handler_version(self):
        self.channel.get_latest_version()

    @pyqtSlot(str, str)
    def js_handler_login(self, email, password):
        """
        Method is called from js.
        """
        self.window.start_manager(email, password)

    @pyqtSlot(str)
    def js_handler_reset_password(self, email):
        url = "https://hprox.com/api/account/password/reset/"
        requests.post(url, data=dict(email=email))

    @pyqtSlot(str)
    def js_open_url(self, url):
        self.window.open_url(url)


class Window(hpxqt_mng.WindowManagerMixIn,
             QWebEngineView):

    signal_minimize_tray = pyqtSignal()

    def __init__(self):
        super(hpxqt_mng.WindowManagerMixIn, self).__init__()
        super(Window, self).__init__()

        self.signal_minimize_tray.connect(self.action_minimize_tray)

        self.media = hpxqt_utils.get_media_dir_path()
        self.templates = hpxqt_utils.get_templates_dir_path()
        self.db_path = hpxqt_utils.get_db_file_path()

        self.channel = QWebChannel(self.page())
        self.router = Router(window=self)
        self.channel.registerObject("router", self.router)
        self.page().setWebChannel(self.channel)

        self.name = 'hproxy'
        self.setWindowTitle("hprox.com")
        self.resize(400, 480)
        self.setWindowIcon(QIcon(os.path.join(self.media, 'images', 'icon.png')))

        self._create_tray_icon()
        self.trayIcon.show()

    def closeEvent(self, event):
        close = QMessageBox()
        close.setText("Are you sure?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()

    def close(self, *args):
        self.router.init_close.emit()
        QApplication.instance().quit()

    def action_logout(self):
        self.router.init_close.emit()
        self.router.db_manager.delete_user()
        self.close()

    def action_minimize_tray(self):
        self.set_status_traymenu(is_disabled=False)
        self.hide()

    def _read_html_file(self, file):
        path_file = os.path.join(self.templates, file)

        if not file.split('.')[-1] == 'html':
            raise ValueError('{} is not html file.'.format(file))

        with open(path_file, 'r') as html:
            first_line = html.readline()
            if not '<!DOCTYPE html>' in str(first_line):
                raise ValueError('{} is not correct format.'.format(file))

        return QUrl().fromLocalFile(path_file)

    def load_login_page(self):
        user = self.router.db_manager.last_user()
        obj = self._read_html_file('login.html')
        self.load(obj)

        if user:
            self.router.js_handler_login(user.email, user.password)

    def show_error(self, error_msg):
        self.manager_thread.exit()

        # Wake up QT Thread - otherwise throws error
        # that `show_error` JS function not found.
        time.sleep(0.01)
        
        self.page().runJavaScript("show_error('%s');" % error_msg)

    def open_url(self, url):
        _url = QUrl(url)
        if not QDesktopServices.openUrl(_url):
            QMessageBox.warning(self, 'Open Url', 'Could not open url')

    def open_help(self):
        self.open_url('https://hprox.com/dash/how-to-proxy/')

    def open_preferences(self):
        self.open_url('https://hprox.com/dash/proxy')

    def open_lost_password(self):
        self.open_url('https://hprox.com/dash/proxy')

    def open_create_account(self):
        self.open_url('https://hprox.com/dash/proxy')

    def set_status_traymenu(self, is_disabled):
        # self.upgrade.setDisabled(is_disabled)
        self.preference.setDisabled(is_disabled)
        self.logout.setDisabled(is_disabled)

    def _create_tray_icon(self):
        """ Creates initial tray icon with the minimum options.
        """

        self.trayIconMenu = QMenu(self)
        self.trayIcon = QSystemTrayIcon(self)
        icon = QIcon(os.path.join(self.media, 'images', 'icon.png'))
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)

        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.label_balance = QAction('Balance: unknown', self)
        self.label_balance.setDisabled(True)
        self.trayIconMenu.addAction(self.label_balance)
        self.trayIconMenu.addSeparator()

        #self.label_status = QAction('Status: unkown', self)
        #self.label_status.setDisabled(True)
        #self.trayIconMenu.insertAction(self.quitAction, self.label_status)

        #self.trayIconMenu.addSeparator()

        #self.upgrade = QAction('Upgrade', self, triggered=self.getUpgrade)
        #self.trayIconMenu.addAction(self.upgrade)

        self.trayIconMenu.addSeparator()

        self.preference = QAction('Preferences', self, triggered=self.open_preferences)
        self.trayIconMenu.addAction(self.preference)

        self.help = QAction('Help', self, triggered=self.open_help)
        self.trayIconMenu.addAction(self.help)
        self.trayIconMenu.addSeparator()

        self.logout = QAction('Logout', self, triggered=self.action_logout)
        self.trayIconMenu.addAction(self.logout)

        self.quitAction = QAction("&Quit", self, triggered=self.close)
        self.trayIconMenu.addAction(self.quitAction)

        self.set_status_traymenu(is_disabled=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Systray", "I couldn't detect any system tray on this system.")
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    window = Window()
    window.show()
    window.load_login_page()
    sys.exit(app.exec_())
