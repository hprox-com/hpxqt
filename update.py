import os
import sys
import platform

from PyQt5.QtCore import pyqtSignal


if getattr(sys, 'frozen', False):
    FOLDER = os.path.dirname(sys.executable)
elif __file__:
    FOLDER = os.path.dirname(__file__)

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


#    def app_handler_download_new_version(self, file):
#        downloader = DownloadThread(url, file)
#        downloader.data_downloaded.connect(self.handle_downloaded_new_version)
#        downloader.start()
#        self.parent.upgrade_to_new_version.emit()
#
#    def handle_downloaded_new_version(self):
#        self.parent.upgrade_to_new_version.emit()


class WindowUpdateMixIn(object):
    signal_upgrade_to_new_version = pyqtSignal()

    def __init__(self):
        self.signal_upgrade_to_new_version.connect(self.action_upgrade_to_new_version)
        self._OS = platform.system()
        self._ARCH = platform.architecture()[0]


    def _executable_filename(self):
        return os.path.join(FOLDER, 'install' if self._OS == 'Linux' else 'install.exe')

    def action_upgrade_to_new_version(self):
        """
        Updates database and replaces a current process with
        a new process.
        """
        self.setInstaledUpdateToDB()
        print("Start new version")
        os.execv(os.path.join(FOLDER, '{}.exe'.format(self.name)
        if self._OS == 'Windows' else self.name), ('',))


    def getUpgrade(self):
        """
        Downloads upgrade
        """
        self.upgrade.setIconText('Downloading...')
        self.upgrade.setDisabled(True)
        self.router.get_upgrade.emit(self._executable_filename())

    def setNewVersion(self, version):
        """
        Sets text version for app or enables
        a button for upgrade.
        """
        last_update = self.getLastUpdateFromDB()
        update = self.getUpdateFromDB(version)
        if last_update:
            if update and update.is_installed:
                self.upgrade.setIconText('Version {}'.format(update.version))
                self.upgrade.setDisabled(True)
            elif not update:
                self.upgrade.setIconText('Upgrade...')
                self.upgrade.setDisabled(False)
                self.addUpdateToDB(version)
            elif not update.is_installed:
                self.upgrade.setIconText('Upgrade...')
                self.upgrade.setDisabled(False)
        elif not last_update and version:
            self.addUpdateToDB(version, True)
            self.upgrade.setIconText('Version {}'.format(version))
            self.upgrade.setDisabled(True)

    def refresh_status(self):
        """
        Refresh all protocols status
        """
        list_apps = ['fetcher', 'manager', 'bridge']
        self.label_status.setText("Manager: %s | Fetcher: %s | Listener: %s" % (1, 2, 3))

    def checkUpgrade(self):
        """ Sends request a new version
        """
        self.router.get_latest_version.emit()
