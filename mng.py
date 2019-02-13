import asyncio

from PyQt5.QtCore import QThread

from hpxclient.mng import service as mng_service
from hpxqt import consumers as hpxqt_consumers


class TCPManagerThread(QThread):
    """Thread for manager service."""
    def __init__(self, email, password):
        QThread.__init__(self)
        self.email = email
        self.password = password
        self.loop = asyncio.get_event_loop()

    def run(self):
        coro = mng_service.start_client(
            email=self.email,
            password=self.password,
            message_handler=hpxqt_consumers.process_message)

        asyncio.ensure_future(coro, loop=self.loop)

        if self.loop.is_running():
            return

        self.loop.run_forever()

    def stop(self):
        pending = asyncio.Task.all_tasks()
        for p in pending:
            p.cancel()
        self.loop.stop()


class WindowManagerMixIn(object):
    def __init__(self):
        self.manager_thread = None

    def start_manager(self, email, password):
        self.manager_thread = TCPManagerThread(email, password)
        self.manager_thread.start()
        print("Start manager", id(self), self.manager_thread)

    def stop_manager(self):
        self.manager_thread.stop()
