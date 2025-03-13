import asyncio
import json
import logging
import sqlite3
from enum import Enum
from threading import Thread

import aiosqlite

from beusproxy.config import DATABASE
from beusproxy.services.telegram import send_message
from bot.common.utils import report_gen_md


async def query(
        sql, *args, commit=False, fetchall=True, fetchone=False
):
    """Aiosqlite query execution wrapper"""
    async with aiosqlite.connect(DATABASE) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(sql, args) as cursor:
            if commit:
                if cursor.total_changes > 0:
                    await conn.commit()
                else:
                    await conn.rollback()
            if fetchone:
                return await cursor.fetchone()
            if fetchall:
                return await cursor.fetchall()


async def get_sub(sub_id) -> sqlite3.Row | list[sqlite3.Row]:
    """Get Subscriptions Coroutine

    Args:
        sub_id (int): Subscriber ID

    Returns:
        - list: List of Rows
        - sqlite3.Row: Row
    """
    return await query("""
        SELECT
            tgs.telegram_chat_id,
            ems.email,
            dcs.discord_webhook_url
        FROM
            Students s
        LEFT JOIN
            Telegram_Subscribers tgs
        ON
            s.id == tgs.owner_id AND
            s.active_telegram_id == tgs.telegram_id
        LEFT JOIN
            Email_Subscribers ems
        ON
            s.id == ems.owner_id AND
            s.active_email_id == ems.email_id
        LEFT JOIN
            Discord_Subscribers dcs
        ON
            s.id == dcs.owner_id AND
            s.active_discord_id == dcs.discord_id
        WHERE
            s.id = ?;
    """, sub_id, fetchone=True)


async def notify_coro(sub_id, diffs, grades, *, httpc):
    sub = await get_sub(sub_id)

    logging.getLogger(__package__).debug("Rendered:\n%s", report_gen_md(diffs, grades))
    if sub["telegram_chat_id"]:
        send_message(
            report_gen_md(diffs, grades),
            sub["telegram_chat_id"],
            params = {
                "parse_mode": "MarkdownV2"
            },
            httpc=httpc
        )
    if sub["email"]:
        pass
    if sub["discord_webhook_url"]:
        pass

    logging.debug("Sub %d: %s", sub_id, json.dumps(dict(sub), indent=1))


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
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Clean up the manager"""
        self._loop.stop()

    def notify(self, sub_id, diffs, grades):
        """Notify Asynchronously

        Args:
            sub_id (int): Subscriber ID
            diffs (dict): Differences
            grades (dict): Grades

        Returns:
            Future: Future object
        """

        self.submit_coro(notify_coro, sub_id, diffs, grades, httpc=self._httpc).result()

    def submit_coro(self, task, *args, **kwargs):
        """Thread-safe method to submit coroutine task.

        Args:
            task (function): Coroutine

        Returns:
            Future: Future object
        """
        return asyncio.run_coroutine_threadsafe(task(*args, **kwargs), self._loop)

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
