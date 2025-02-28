from queue import Queue
from threading import Event, Thread


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

    def notify(self, notification):
        """Notify"""
        # notify_parser(notification)


class Notification:
    """Notification Model"""

    def __init__(self, *, service=None):
        self.service = service
