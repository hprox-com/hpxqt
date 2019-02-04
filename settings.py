import os
import pathlib

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(PROJECT_DIR, 'templates')

MEDIA_DIRS = os.path.join(PROJECT_DIR, 'media')

USER_DIR = str(pathlib.Path.home())

HPROXY_DIR = os.path.join(USER_DIR, '.hproxy')

if not os.path.exists(HPROXY_DIR):
    os.mkdir(HPROXY_DIR)


DB_FILE = os.path.join(HPROXY_DIR, 'db.sqlite3')
