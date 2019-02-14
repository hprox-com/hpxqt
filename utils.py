import os
import pathlib
import sys
import tarfile
import zipfile
from decimal import Decimal

import psutil
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication
from hpxqt import consts as hpxqt_consts
from hpxclient import consts as hpxclient_consts


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


def extract_zip(fpath):
    with zipfile.ZipFile(fpath) as zip:
        zip.extractall()


def extract_tar(fpath):
    with tarfile.open(fpath) as tar:
        tar.extractall()
        

def get_executable_linux(fpath):
    for root, dirs, files in os.walk(fpath):
        for file in files:
            if hpxqt_consts.LINUX_APP_NAME not in file:
                continue
            return os.path.join(root, file)


def restart_program():
    try:
        cur_process = psutil.Process(os.getpid())
        open_files = cur_process.open_files() + cur_process.connections()
        for file in open_files:
            os.close(file.fd)
    except Exception as e:
        print(e)
    py_exec = sys.executable
    os.execl(py_exec, py_exec, *sys.argv)
