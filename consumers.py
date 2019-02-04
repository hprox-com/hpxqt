from decimal import Decimal

from hpxclient import protocols as protocols
from hpxclient import consts as hpxclient_consts


class AuthResponseConsumer(object):
    KIND = protocols.AuthResponseProducer.KIND

    def process(self, service, msg):
        error = msg[b"error"]
        if error:
            print("ERROR", error)
            service.window.show_error(error_msg=error.decode())
            service.window.stop_manager()
            service.db_manager.delete_user(service.email)
        else:
            service.is_authorized = True
            service.db_manager.add_user(email=service.email,
                                        password=service.password)
            service.window.signal_minimize_tray.emit()


class InfoBalanceConsumer(object):
    KIND = protocols.InfoBalanceConsumer.KIND

    def process(self, service, msg):
        service.balance_amount = Decimal(str(msg[b"balance_amount"])) / (
        10 ** hpxclient_consts.HPX_NUMBER_OF_DECIMALS)
        service.window.label_balance.setText("Balance: %s BST" % service.balance_amount)


class InfoVersionConsumer(object):
    KIND = protocols.InfoVersionConsumer.KIND

    def process(self, service, msg):
        service.latest_version = msg[b"version"].decode()
