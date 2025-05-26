import os
import time
from multiprocessing import Event, Process
from pathlib import Path

import schedule

from beusproxy.common.utils import get_logger
from beusproxy.services.httpclient import HTTPClient
from . import run_chain

logger = get_logger(__package__)


class BotProc:
    """Bot Process Base Class"""

    def __init__(self, daemon=True, shevent=Event()):
        self._shevent = shevent
        self._proc = None
        self._daemon = daemon
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

        if daemon:
            self._proc = Process(target=proc_worker, args={self._shevent}, daemon=daemon)
            self._proc.start()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def run(self):
        if not self._daemon:
            proc_worker(shevent=self._shevent)

    def close(self):
        """Terminates Bot Process"""
        if self._proc:
            self._shevent.set()
            self._proc.join()
            if self._lock_file.exists():
                self._lock_file.unlink()


def proc_worker(shevent=None):
    httpc = HTTPClient(trust_env=True)
    schedule.every(2).minutes.do(run_chain, httpc)
    while not shevent.is_set():
        schedule.run_pending()
        time.sleep(1)
    schedule.clear()
    httpc.close()
