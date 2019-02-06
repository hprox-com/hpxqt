from hpxclient import protocols as protocols
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

    def process(self, msg):
        self.window.latest_version = msg[b"version"].decode()



REGISTERED_CONSUMERS = [
    AuthResponseConsumer,
    InfoBalanceConsumer,
    InfoVersionConsumer
]


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
