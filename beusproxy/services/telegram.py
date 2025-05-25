import math
import re
import time
from datetime import datetime
from sqlite3 import Error
from threading import Event, Thread
from typing import Optional

from aiohttp import ClientError
from jinja2 import Environment

from ..common.utils import get_logger
from ..config import (
    BOT_TELEGRAM_API_KEY,
    BOT_TELEGRAM_HOSTNAME,
    POLLING_TIMEOUT,
    REQUEST_TIMEOUT,
    WEB_HOSTNAME,
)
from .database import get_db
from .httpclient import HTTPClient, HTTPClientError

logger = get_logger(__name__)


class TelegramClient:
    # pylint: disable=R0902
    # pylint: disable=R0913
    """Telegram base class.
    Getting updates, sending messages
    """

    def __init__(
        self,
        http_client: HTTPClient,
        jinja_env: Environment,
        *,
        request_timeout=REQUEST_TIMEOUT,
        polling_timeout=POLLING_TIMEOUT,
        api_hostname=BOT_TELEGRAM_HOSTNAME,
        api_key=BOT_TELEGRAM_API_KEY,
        worker_name: Optional[str] = None,
    ):
        self._jinja_env = jinja_env
        self._httpc = http_client
        self._request_timeout = request_timeout
        self._polling_timeout = polling_timeout
        self._api_hostname = api_hostname
        self._api_key = api_key
        self._offset = None

        def updates_thread():
            # pylint: disable=W3101
            """Telegram Updates Thread"""
            while not self._shevent.is_set():
                try:
                    res = self._httpc.request(
                        "GET",
                        f"https://{api_hostname}/bot{api_key}/getUpdates",
                        params={
                            k: v
                            for k, v in {
                                "offset": self._offset,
                                "timeout": self._polling_timeout,
                            }.items()
                            if v is not None
                        },
                        timeout=None,
                    )
                    if res.status == 200:
                        for u in self._httpc.cr_json(res)["result"]:
                            self._offset = u["update_id"] + 1
                            self.process_update(u)
                    else:
                        logger.error("Error while getting updates")
                        time.sleep(self._request_timeout)
                except TimeoutError as e:
                    logger.error(e)
            logger.info("TelegramClient shutting down...")

        self._shevent = Event()
        self._worker = Thread(name=worker_name, target=updates_thread, daemon=True)
        self._worker.start()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        """Close TelegramClient"""
        self._shevent.set()

    def start_cmd(self, chat_id, user_id):
        """/start command logic.
        Shows welcome message.

        Args:
            chat_id (int): Telegram Chat ID
            user_id (str): Telegram user_id
        """
        logger.debug("User '@%s' issued start command", user_id)
        send_template(
            "start", chat_id, user_id, httpc=self._httpc, jinja_env=self._jinja_env
        )

    def help_cmd(self, chat_id, user_id):
        """/help command logic.
        Shows help message.

        Args:
            chat_id (int): Telegram Chat ID
            user_id (str): Telegram user_id
        """
        logger.debug("User '@%s' issued help command", user_id)
        send_template(
            "help",
            chat_id,
            user_id,
            WEB_HOSTNAME,
            httpc=self._httpc,
            jinja_env=self._jinja_env,
        )

    def verify_cmd(self, params, user_id, chat_id):
        """/verify command logic.
        Verifies 6-digit code.

        Args:
            params (str): Parameters after the command
            user_id (str): Telegram User ID
            chat_id (int): Telegram Chat ID
        """
        m = re.match(r".*(\d{6})", params)
        if m is None:
            send_template(
                "verify_empty",
                chat_id,
                user_id,
                httpc=self._httpc,
                jinja_env=self._jinja_env,
            )
            return
        logger.info("User '@%s' tried to verify code: %s", user_id, m.group(1))

        with get_db() as db_con:
            db_cur = db_con.cursor()
            db_res = db_cur.execute(
                """
                SELECT
                    owner_id,
                    verify_date
                FROM
                    Verifications
                WHERE
                    verified = FALSE AND
                    verify_service = 0 AND
                    verify_code = ?
                ORDER BY verify_date DESC;
            """,
                (m.group(1),),
            ).fetchone()
            if not db_res:
                send_template(
                    "verify_invalid",
                    chat_id,
                    user_id,
                    httpc=self._httpc,
                    jinja_env=self._jinja_env,
                )
                logger.info(
                    "User '@%s' is not registered or sent an invalid code.", user_id
                )
                return

            owner_id = db_res["owner_id"]

            if (
                math.floor(
                    (
                        datetime.now() - datetime.fromisoformat(db_res["verify_date"])
                    ).total_seconds()
                    / 60
                )
                > 9
            ):
                send_template(
                    "verify_expired",
                    chat_id,
                    user_id,
                    httpc=self._httpc,
                    jinja_env=self._jinja_env,
                )
                logger.info("User '@%s'`s verification code has been expired")
                return

            db_cur.execute(
                """
                UPDATE
                    Verifications
                SET
                    verified = TRUE,
                    verify_item = ?
                WHERE
                    verify_code = ? AND
                    verify_service = 0 AND
                    verified = FALSE;
            """,
                (user_id, m.group(1)),
            )
            db_con.commit()

            db_res = db_cur.execute(
                """
                INSERT INTO
                    Telegram_Subscribers
                (owner_id, telegram_user_id, telegram_chat_id)
                VALUES
                    (?, ?, ?)
                RETURNING
                    telegram_id;
            """,
                (owner_id, user_id, chat_id),
            ).fetchone()

            if not db_res:
                db_con.rollback()
                logger.error(
                    "Couldn't insert a telegram subscription: (%d, %d, %s)",
                    owner_id,
                    chat_id,
                    user_id,
                )

            telegram_id = db_res["telegram_id"]
            db_con.commit()

            db_res = db_cur.execute(
                """
                UPDATE Students
                SET active_telegram_id = ?
                WHERE id = ?
            """,
                (telegram_id, owner_id),
            )

            if not db_res.rowcount > 0:
                db_con.rollback()
                logger.error(
                    "Couldn't update student's active telegram subscription: (%d, %d)",
                    owner_id,
                    telegram_id,
                )

            send_template(
                "verify_success",
                chat_id,
                user_id,
                httpc=self._httpc,
                jinja_env=self._jinja_env,
            )
            db_con.commit()

    def unsubscribe(self, chat_id, user_id):
        """Unsubscribes user

        Args:
            chat_id (int): Telegram Chat ID
            user_id (str): Telegram user_id
        """
        db_con = get_db()
        db_cur = db_con.cursor()

        db_res = db_cur.execute(
            """
            UPDATE
                Students
            SET
                active_telegram_id = NULL
            WHERE
                active_telegram_id IN (
                    SELECT
                        ts.telegram_id
                    FROM
                        Telegram_Subscribers ts
                    WHERE
                        ts.telegram_user_id = ? AND
                        ts.telegram_chat_id = ?
                );
        """,
            (user_id, chat_id),
        )

        if not db_res.rowcount > 0:
            db_con.rollback()
            send_template(
                "unsubscribe_nosub",
                chat_id,
                user_id,
                WEB_HOSTNAME,
                httpc=self._httpc,
                jinja_env=self._jinja_env,
            )
            logger.info(
                "Couldn't unsubscribe for telegram user '@%s'. No subscriptions",
                user_id,
            )
            return

        db_con.commit()
        send_template(
            "unsubscribe",
            chat_id,
            user_id,
            httpc=self._httpc,
            jinja_env=self._jinja_env,
        )
        logger.info("Telegram user '@%s' unsubscribed", user_id)

    def process_update(self, u):
        """Process verifications queue

        Args:
            u (dict): Update object
        """
        if u.get("message"):
            if not u["message"]["chat"]["type"] == "private":
                return
            if (
                u["message"].get("text")
                and u["message"].get("entities")
                and u["message"].get("from")
            ):
                inx = None
                for i, e in enumerate(u["message"]["entities"]):
                    if (
                        e["type"] == "bot_command"
                        or not e.get("url", "").find("bot_command") == -1
                    ):
                        inx = i
                if inx is None:
                    return
                m = re.match(r"/(\w+)(.*)", u["message"].get("text", ""))
                if m is None:
                    return
                chat_id = u["message"]["chat"]["id"]
                user_id = u["message"]["from"]["id"]
                try:
                    match m.group(1):
                        case "start":
                            self.start_cmd(chat_id, user_id)
                        case "help":
                            self.help_cmd(chat_id, user_id)
                        case "verify":
                            self.verify_cmd(m.group(2), user_id, chat_id)
                        case "unsubscribe":
                            self.unsubscribe(chat_id, user_id)
                except Error as e:
                    logger.error(e)


def get_me(*, httpc):
    """Telegram API: getMe

    Returns:
        dict: JSON response
    """
    res = httpc.request(
        "GET", f"https://{BOT_TELEGRAM_HOSTNAME}/bot{BOT_TELEGRAM_API_KEY}/getMe"
    )

    if not res.status == 200:
        raise ClientError(res.status)

    return httpc.cr_json(res)


def send_message(text=None, chat_id=None, *, params=None, httpc):
    """Telegram API: sendMessage

    Args:
        text (str): Text message
        chat_id (int): Telegram Chat ID
        params (dict): sendMessage parameters
        httpc (HTTPClient): HTTP Client
    """
    if params is None:
        params = {}
    if text:
        params["text"] = text
    if chat_id:
        params["chat_id"] = chat_id
    res = httpc.request(
        "GET",
        f"https://{BOT_TELEGRAM_HOSTNAME}/bot{BOT_TELEGRAM_API_KEY}/sendMessage",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )

    if not res.status == 200:
        raise HTTPClientError(res.status, httpc.cr_text(res))

    return httpc.cr_json(res)


def send_template(template, chat_id, *args, httpc, jinja_env):
    """Telegram API Wrapper.
    Send template messages

    Args:
        template (str): Template key
        chat_id (int): Telegram Chat ID
        httpc (HTTPClient): HTTP Client
        jinja_env (Environment): Jinja2 Environment
    """
    logger.debug("Sent template '%s' to chat %d'", template, chat_id)
    send_message(
        jinja_env.get_template(f"{template}.txt").render(args=args),
        chat_id,
        httpc=httpc,
    )
