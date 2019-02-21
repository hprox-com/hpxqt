import logging
import os
import pathlib
import platform
import sys
from decimal import Decimal
from zipfile import ZipFile, ZipInfo

from PyQt5.QtWidgets import QApplication

from hpxclient import consts as hpxclient_consts
from hpxqt import consts as hpxqt_consts

SATOSHI_WEIGHT = 100000000


def satoshi2bst(amount):
    return Decimal(str(amount)) / SATOSHI_WEIGHT


def get_os():
    _os = platform.system().lower()
    if _os == 'darwin':
        _os = hpxqt_consts.MAC_OS
    return _os


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


def get_app_dir():
    app_dir = None
    if getattr(sys, 'frozen', False):
        app_dir = sys.executable
    elif __file__:
        app_dir = __file__
    app_dir = os.path.dirname(os.path.abspath(app_dir))

    if get_os() == hpxqt_consts.MAC_OS:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(app_dir)))
    return app_dir


def get_templates_dir_path():
    return os.path.join(get_data_dir(), 'templates')


def get_media_dir_path():
    return os.path.join(get_data_dir(), 'media')


def get_hprox_dir_path():
    home = str(pathlib.Path.home())

    hprox_dir = os.path.join(home, hpxclient_consts.HPROX_DIR_NAME)
    if not os.path.exists(hprox_dir):
        os.mkdir(hprox_dir)

    return hprox_dir


def get_db_file_path():
    return os.path.join(get_hprox_dir_path(), 'db.sqlite3')


def get_main_window():
    return QApplication.instance()._hprox_main_window


def convert_bytes(data):
    if isinstance(data, bytes): return data.decode('ascii')
    if isinstance(data, dict): return dict(map(convert_bytes, data.items()))
    if isinstance(data, tuple): return tuple(map(convert_bytes, data))
    if isinstance(data, list): return list(map(convert_bytes, data))
    return data


def restart_program():
    try:
        sys.stdout.flush()
    except Exception as e:
        print(e)

    app_exec, *app_args = sys.argv
    if get_os() == hpxqt_consts.MAC_OS:
        app_args.insert(0, os.path.abspath(app_exec))
    os.execl(sys.executable, sys.executable, *app_args)


class ZipFileWithPermissions(ZipFile):
    """ Custom ZipFile class handling file permissions."""

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath


def get_logging_config():
    return dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            'default': {
                'format': '[{levelname}] [{asctime}]: {message}',
                'style': '{'
            },
            'plain': {
                'format': '{message}',
                'style': '{'
            }
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': logging.DEBUG
            },
            'file': {
                'class': 'logging.FileHandler',
                'formatter': 'plain',
                'level': logging.INFO,
                'filename': os.path.join(get_hprox_dir_path(), 'info.log'),
                'mode': 'w',
            },
        },
        loggers={
            'hpxqt': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True
            },
            'hpxqt.file': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': True
            }
        }
    )


def get_loggers():
    return logging.getLogger('hpxqt'), logging.getLogger('hpxqt.file')
