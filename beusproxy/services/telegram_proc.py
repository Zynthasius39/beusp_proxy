import os
import time
from multiprocessing import Event, Process
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..common.utils import get_logger
from ..config import TEMPLATES_FOLDER
from .httpclient import HTTPClient
from .telegram import TelegramClient


class TelegramProc:
    """Telegram Process Base Class"""

    def __init__(self):
        self._shevent = Event()
        self._proc = None
        self._lock_file = Path(".telegram.lock")
        if not self._lock_file.exists():
            self._lock_file.write_text(str(os.getpid()), encoding="UTF-8")
            time.sleep(1)
            if self._lock_file.read_text(encoding="UTF-8") == str(os.getpid()):
                get_logger(__package__).info("Telegram Process spawned - PID:%d", os.getpid())
            else:
                return
        else:
            return

        def proc_init():
            tc = TelegramClient(
                HTTPClient(trust_env=True),
                Environment(loader=FileSystemLoader(TEMPLATES_FOLDER)),
            )
            while not self._shevent.is_set():
                try:
                    time.sleep(2)
                except KeyboardInterrupt:
                    self._shevent.set()
                    tc.close()
            tc.close()

        self._proc = Process(target=proc_init)
        self._proc.start()

    def close(self):
        """Close Telegram Connection"""
        if self._proc:
            self._shevent.set()
            self._proc.join()
            if self._lock_file.exists():
                self._lock_file.unlink()
