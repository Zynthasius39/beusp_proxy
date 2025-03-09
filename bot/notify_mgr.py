from enum import Enum
from queue import Queue
from threading import Event, Thread

from .common.utils import notify_parser


class NotifyManager:
    """Notification Manager Base Class"""

    def __init__(self):
        self._shevent = Event()
        self._queue = Queue()

        def nm_worker():
            """Thread worker"""
            while not self._shevent.is_set():
                u = self._queue.get(timeout=5)
                print(u)

        self._thread = Thread(target=nm_worker, daemon=True)
        self._thread.start()

    def notify(self, sub_id, diffs):
        """Notify"""
        for n in notify_parser(sub_id, diffs):
            self._queue.put(n)


class Notification:
    """Notification Model"""

    def __init__(self, *, service, destination=None):
        self.service = service
        self.destination = destination


class SubService(Enum):
    """Subscription Service Enum"""

    TELEGRAM = 0
    DISCORD = 1
    EMAIL = 2
