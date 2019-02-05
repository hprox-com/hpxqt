import asyncio
import os
import platform
import time

import requests
import sys

from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import (QObject, pyqtSlot, QThread, pyqtSignal, QUrl)
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QAction, QApplication, QSystemTrayIcon, QMessageBox, QMenu)
from hpxclient.mng.service import start_client

from hpxqt import consumers as qt_consumers
from hpxqt import settings
from hpxqt.database import DatabaseManager

from pony.orm.dbproviders import sqlite  # it is needed to pyinstaller


#if getattr(sys, 'frozen', False):
#    FOLDER = os.path.dirname(sys.executable)
#elif __file__:
#    FOLDER = os.path.dirname(__file__)
#
#
#class DownloadThread(QThread):
#
#    signal_download_finished = pyqtSignal()
#
#    def __init__(self, url, filename):
#        QThread.__init__(self)
#        self.url = url
#        self.filename = filename
#
#    def __del__(self):
#        self.wait()
#
#    def run(self):
#        response = requests.get(self.url, stream=True)
#        if response.status_code != 200:
#            return
#
#        with open(self.filename, 'wb') as f:
#            for chunk in response.iter_content(chunk_size=1024):
#                if chunk:  # filter out keep-alive new chunks
#                    f.write(chunk)
#                    # f.flush() commented by recommendation from J.F.Sebastian
#        self.signal_download_finished.emit()


class AuthThread(QThread):
    """ Thread for manager service
    """

    def __init__(self, loop, email, password, router):
        QThread.__init__(self)
        self.email = email
        self.password = password
        self.loop = loop
        self.router = router
        self.manager = None

    def __del__(self):
        self.wait()

    def run(self):
        self.manager = asyncio.ensure_future(start_client(email=self.email,
                                                          password=self.password,
                                                          ui=self.router),
                                             loop=self.loop)

        if self.loop.is_running():
            return
        self.loop.run_forever()
        

class Router(QObject):
    """
    Class for connection web, main widgets and network mangers.
    Methods which are called from js file start with 'js_' and
    from Managers start with 'network_' and from main app start with 'app_'.
    """

    init_close = pyqtSignal()

    REGISTERED_CONSUMERS = [
        qt_consumers.AuthResponseConsumer,
        qt_consumers.InfoBalanceConsumer,
        qt_consumers.InfoVersionConsumer
    ]

    def __init__(self, window):
        super(Router, self).__init__()
        self.window = window

        self.email = None
        self.password = None
        self.channel = None
        self.TIMEOUT = 10

        # Threads for network services
        self.manager_thread = None

        self.init_close.connect(self.app_handler_close_connection)

        self.db_manager = DatabaseManager()
        self.db_manager.initialize()

        self.loop = asyncio.get_event_loop()
        
    def app_handler_close_connection(self):
        if self.channel:
            self.channel.close_connections()

    def app_handler_version(self):
        self.channel.get_latest_version()

#    def app_handler_download_new_version(self, file):
#        url = 'file:///home/denis/PycharmProjects/pyqt/interface'
#        downloader = DownloadThread(url, file)
#        downloader.data_downloaded.connect(self.handle_downloaded_new_version)
#        downloader.start()
#        self.parent.upgrade_to_new_version.emit()
#
#    def handle_downloaded_new_version(self):
#        self.parent.upgrade_to_new_version.emit()

    @pyqtSlot(str, str)
    def js_handler_login(self, email, password):
        """
        Method is called from js.
        """
        self.email = email
        self.password = password
        self.manager_thread = AuthThread(self.loop, email, password, self)
        self.manager_thread.start()

    @pyqtSlot(str)
    def js_handler_reset_password(self, email):
        url = "https://hprox.com/api/account/password/reset/"
        data = {"email": email, }
        requests.post(url, data=data)

    @pyqtSlot(str)
    def js_open_url(self, url):
        self.window.open_url(url)

    def process_message(self, msg):
        """ All messages sent to the manager are also processed by
        the ui interface.
        """
        consumer_cls = None
        consumer_kind = msg[b'kind'].decode()

        for _consumer_cls in self.REGISTERED_CONSUMERS:
            if consumer_kind == _consumer_cls.KIND:
                consumer_cls = _consumer_cls
                break
        if consumer_cls is None:
            raise Exception('Kind not recognized %s, available: %s' % (consumer_kind, self.REGISTERED_CONSUMERS))
        return consumer_cls().process(self, msg[b'data'])


class Window(QWebEngineView):

    signal_minimize_tray = pyqtSignal()
    signal_upgrade_to_new_version = pyqtSignal()

    def __init__(self):
        super(Window, self).__init__()

        self.signal_minimize_tray.connect(self.action_minimize_tray)
        #self.signal_upgrade_to_new_version.connect(self.action_upgrade_to_new_version)

        self.media = settings.get_media_dir_path()
        self.templates = settings.get_templates_dir_path()
        self.db_path = os.path.join(settings.HPROXY_DIR, 'db')

        self.channel = QWebChannel(self.page())
        self.router = Router(window=self)
        self.channel.registerObject("router", self.router)
        self.page().setWebChannel(self.channel)
        ################################################

        self._OS = platform.system()
        self._ARCH = platform.architecture()[0]
        self.name = 'hproxy'

        self.load_login_page()

        self.setWindowTitle("Hprox.com")
        self.resize(400, 480)
        self._create_tray_icon()
        self.trayIcon.show()
        self.setWindowIcon(QIcon(os.path.join(self.media, 'images', 'Desktop_icon.png')))

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
        self.router.db_manager.delete_user(self.router.email)
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

    def stop_manager(self):
        loop = asyncio.get_event_loop()
        loop.stop()
        self.router.manager_thread.exit()

#    def _executable_filename(self):
#        return os.path.join(FOLDER, 'install' if self._OS == 'Linux' else 'install.exe')

    def load_login_page(self):
        user = self.router.db_manager.last_user()
        obj = self._read_html_file('login.html')
        self.load(obj)

        if user:
            self.router.js_handler_login(user.email, user.password)

    def show_error(self, error_msg):
        self.router.manager_thread.exit()
        
        # Wake up QT Thread - otherwise throws error
        # that `show_error` JS function not found.
        time.sleep(0.01)
        
        self.page().runJavaScript("show_error('%s');" % error_msg)

#    def action_upgrade_to_new_version(self):
#        """
#        Updates database and replaces a current process with
#        a new process.
#        """
#        self.setInstaledUpdateToDB()
#        print("Start new version")
#        os.execv(os.path.join(FOLDER, '{}.exe'.format(self.name)
#        if self._OS == 'Windows' else self.name), ('',))

#
#    def getUpgrade(self):
#        """
#        Downloads upgrade
#        """
#        self.upgrade.setIconText('Downloading...')
#        self.upgrade.setDisabled(True)
#        self.router.get_upgrade.emit(self._executable_filename())
#
#    def setNewVersion(self, version):
#        """
#        Sets text version for app or enables
#        a button for upgrade.
#        """
#        last_update = self.getLastUpdateFromDB()
#        update = self.getUpdateFromDB(version)
#        if last_update:
#            if update and update.is_installed:
#                self.upgrade.setIconText('Version {}'.format(update.version))
#                self.upgrade.setDisabled(True)
#            elif not update:
#                self.upgrade.setIconText('Upgrade...')
#                self.upgrade.setDisabled(False)
#                self.addUpdateToDB(version)
#            elif not update.is_installed:
#                self.upgrade.setIconText('Upgrade...')
#                self.upgrade.setDisabled(False)
#        elif not last_update and version:
#            self.addUpdateToDB(version, True)
#            self.upgrade.setIconText('Version {}'.format(version))
#            self.upgrade.setDisabled(True)

#    def refresh_status(self):
#        """
#        Refresh all protocols status
#        """
#        list_apps = ['fetcher', 'manager', 'bridge']
#        self.label_status.setText("Manager: %s | Fetcher: %s | Listener: %s" % (1, 2, 3))

#    def checkUpgrade(self):
#        """ Sends request a new version
#        """
#        self.router.get_latest_version.emit()

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
        icon = QIcon(os.path.join(self.media, 'images', 'Desktop_icon.png'))
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
    sys.exit(app.exec_())
