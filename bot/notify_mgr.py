import asyncio
from enum import Enum
from threading import Thread

import aiosqlite

from beusproxy.config import CACHE_DATABASE


class NotifyManager:
    """Notification Manager Base Class"""

    def __init__(self, httpc):
        self._httpc = httpc
        self._loop = asyncio.new_event_loop()

        def nm_worker():
            """Thread worker"""
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = Thread(target=nm_worker, daemon=True)
        self._thread.start()

    def __enter__(self):
        pass

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Clean up the manager"""
        self._loop.stop()

    def notify(self, sub_id, diffs):
        """Notify Asynchronously

        Args:
            sub_id (int): Subscriber ID
            diffs (dict): Differences

        Returns:
            Future: Future object
        """
        return self.submit_coro(self.notify_gen, sub_id, diffs)

    def get_sub_future(self, sub_id, **kwargs):
        """Get Subscriptions Coroutine

        Args:
            sub_id (int): Subscriber ID

        Returns:
            list: List of sqlite3.Row
        """
        return self.submit_coro(
            self.query_coro,
            """
                SELECT
                    active_telegram_id,
                    active_discord_id,
                    active_email_id
                FROM
                    Student_Subscribers
                WHERE
                    id = ?;
            """,
            sub_id,
            **kwargs,
        )

    def submit_coro(self, task, *args, **kargs):
        """Thread-safe method to submit coroutine task.

        Args:
            task (function): Coroutine

        Returns:
            Future: Future object
        """
        return asyncio.run_coroutine_threadsafe(task(*args, **kargs), self._loop)

    def service_coro_gen(self, service_t, diffs):
        """Generate Coroutine to send diffs for the service type

        Args:
            service_t (SubService): Service Type Enum
            diffs (dict): Differences

        Returns:
            coroutine: Sender Coroutine
        """
        # match service_t:
        #     case SubService.TELEGRAM:
        #         pass

    async def notify_gen(self, sub_id, diffs):
        """Notification Parser Coroutine

        Args:
            sub_id (int): Subscriber ID
            diffs (dict): Differences
        """
        # Get sub services, destinations (sub_id)
        sub = self.get_sub_future(sub_id, fetchone=True).result()

        # Parse diffs and send for each service

    async def query_coro(
        self, query, *args, commit=False, fetchall=True, fetchone=False
    ):
        """Coroutine wrapper using aiosqlite"""
        async with aiosqlite.connect(CACHE_DATABASE, uri=True) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, args) as cursor:
                if commit:
                    if cursor.total_changes > 0:
                        await conn.commit()
                    else:
                        await conn.rollback()
                if fetchone:
                    return await cursor.fetchone()
                if fetchall:
                    return await cursor.fetchall()


class Notification:
    """Notification Model"""

    def __init__(self, *, service, destination=None, diff=None):
        self.service = service
        self.destination = destination
        self.diff = diff


class SubService(Enum):
    """Subscription Service Enum"""

    TELEGRAM = 0
    DISCORD = 1
    EMAIL = 2
