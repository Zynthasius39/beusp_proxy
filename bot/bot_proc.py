import logging
import os
import time
from multiprocessing import Event, Process
from pathlib import Path

from beusproxy.services.httpclient import HTTPClient
from bot import run_chain

logger = logging.getLogger(__package__)

class BotProc:
    """Bot Process Base Class"""

    def __init__(self):
        self._shevent = Event()
        self._proc = None
        self._lock_file = Path(".bot.lock")
        if not self._lock_file.exists():
            self._lock_file.write_text(str(os.getpid()), encoding="UTF-8")
            time.sleep(1)
            if self._lock_file.read_text(encoding="UTF-8") == str(os.getpid()):
                logger.info("Bot Process spawned - PID:%d", os.getpid())
            else:
                return
        else:
            return

        def proc_init():
            httpc = HTTPClient()
            while not self._shevent.is_set():
                time.sleep(10)
                run_chain(httpc)
                # TODO: Scheduling

        self._proc = Process(target=proc_init)
        self._proc.start()

    def close(self):
        """Terminates Bot Process"""
        if self._proc:
            self._shevent.set()
            self._proc.join()
            if self._lock_file.exists():
                self._lock_file.unlink()
