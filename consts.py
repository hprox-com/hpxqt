APP_NAME = 'hprox'
APP_TITLE = 'hprox.com'

URL_PREFIX = 'https://hprox.com/'

START_DOWNLOAD = 1
FINISHED_DOWNLOAD = 2
START_INSTALL = 3
FINISHED_INSTALL = 4

LINUX_APP_NAME = 'hprox'
MAC_APP_NAME = 'hprox.app'
WINDOWS_APP_NAME = 'hprox.exe'

ARCH_MAP = {
    '64bit': '64',
    '32bit': '32'
}

MAC_OS = 'osx'
LINUX_OS = 'linux'
WINDOWS_OS = 'windows'

APP_NAME_MAP = dict(
    MAC_OS=MAC_APP_NAME,
    LINUX_OS=LINUX_APP_NAME,
    WINDOWS_OS=WINDOWS_APP_NAME
)
