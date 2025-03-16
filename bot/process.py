import logging
import os
import time
from multiprocessing import Event, Process
from pathlib import Path

import schedule

from beusproxy.services.email import EmailClient
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

        def proc_worker():
            httpc = HTTPClient()
            emailc = EmailClient()
            schedule.every(2).minutes.do(run_chain, httpc, emailc)
            while not self._shevent.is_set():
                schedule.run_pending()
                time.sleep(1)
            schedule.clear()
            emailc.close()
            httpc.close()

        self._proc = Process(target=proc_worker)
        self._proc.start()

    def __enter__(self, *_):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Terminates Bot Process"""
        if self._proc:
            self._shevent.set()
            self._proc.join()
            if self._lock_file.exists():
                self._lock_file.unlink()
