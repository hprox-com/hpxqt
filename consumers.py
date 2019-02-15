import platform

from PyQt5.QtCore import pyqtSlot

from hpxclient import protocols as protocols
from hpxqt import __version__ as version
from hpxqt import consts as hpxqt_consts
from hpxqt import utils as hpxqt_utils


class Consumer(object):
    def __init__(self, window):
        self.window = window


class AuthResponseConsumer(Consumer):
    KIND = protocols.AuthResponseProducer.KIND

    def process(self, msg):
        error = msg[b"error"]
        if error:
            self.window.show()
            self.window.show_error(error_msg=error.decode())
            self.window.stop_manager()
            self.window.router.db_manager.delete_user()
        else:
            self.window.signal_minimize_tray.emit()
            self.window.router.db_manager.add_user(
                email=self.window.manager_thread.email,
                password=self.window.manager_thread.password)


class InfoBalanceConsumer(Consumer):
    KIND = protocols.InfoBalanceConsumer.KIND

    def process(self, msg):
        balance_amount = hpxqt_utils.satoshi2bst(msg[b"balance_amount"])
        self.window.label_balance.setText("Balance: %s BST" % balance_amount)


class InfoVersionConsumer(Consumer):
    KIND = protocols.InfoVersionConsumer.KIND

    def __init__(self, window):
        super().__init__(window)

        self._OS = platform.system().lower()
        if self._OS == 'darwin':
            # to match the mapping returned from response
            self._OS = hpxqt_consts.MAC_OS
        self._ARCH = hpxqt_consts.ARCH_MAP.get(platform.architecture()[0], '')

    def _save_new_version(self, binaries):
        for binary in binaries:
            b_platform = binary['platform'].lower()
            b_arch = binary['arch'].lower()

            if b_platform != self._OS:
                continue

            if b_platform != hpxqt_consts.MAC_OS and (self._ARCH not in b_arch):
                    continue
            return self.window.router.db_manager.add_update(binary['version'],
                                                            binary['file'],
                                                            self._OS)

    def process(self, msg):
        msg = hpxqt_utils.convert_bytes(msg)
        # if version == msg['version']:
        #     return
        
        update_ver = self.window.router.db_manager.get_update(msg["version"])
        if not update_ver:
            update_ver = self._save_new_version(msg['binaries'])
            if not update_ver:
                # There was no update matching system specification
                return

        if update_ver.is_installed:
            return
        self.window.upgrade.setDisabled(False)


REGISTERED_CONSUMERS = [
    AuthResponseConsumer,
    InfoBalanceConsumer,
    InfoVersionConsumer
]


@pyqtSlot(dict)
def process_message(msg):
    """ All messages sent to the manager are also processed by
    the ui interface.
    """

    consumer_cls = None
    consumer_kind = msg[b'kind'].decode()

    for _consumer_cls in REGISTERED_CONSUMERS:
        if consumer_kind == _consumer_cls.KIND:
            consumer_cls = _consumer_cls
            break

    if consumer_cls is None:
        raise Exception('Kind not recognized %s' % consumer_kind)

    window = hpxqt_utils.get_main_window()
    return consumer_cls(window).process(msg[b'data'])
