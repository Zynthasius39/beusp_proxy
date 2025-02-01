import logging
import math
import re
import time
from datetime import datetime

import requests
from jinja2 import Environment, FileSystemLoader

from services.database import get_db
from config import (
    WEB_DOMAIN,
    BOT_TELEGRAM_HOSTNAME,
    BOT_TELEGRAM_API_KEY,
    REQUEST_TIMEOUT,
    POLLING_TIMEOUT
)

jinja_env = Environment(
    loader = FileSystemLoader("src/templates")
)

def get_me():
    """Telegram API: getMe

    Returns:
        dict: JSON response
    """
    res = requests.get(
        f"https://{BOT_TELEGRAM_HOSTNAME}/bot{BOT_TELEGRAM_API_KEY}/getMe",
        timeout = REQUEST_TIMEOUT
    )

    if not res.status_code == 200:
        return None

    return res.json()

def send_message(text, chat_id):
    """Telegram API: sendMessage

    Args:
        text (str): Text message
        chat_id (int): Telegram Chat ID
    """
    res = requests.get(
        f"https://{BOT_TELEGRAM_HOSTNAME}/bot{BOT_TELEGRAM_API_KEY}/sendMessage",
        params = {
            "chat_id": chat_id,
            "text": text
        },
        timeout = REQUEST_TIMEOUT
    )

    if not res.status_code == 200:
        return None

    return res.json()

def send_template(template, chat_id, username, *args):
    """Telegram API Wrapper.
    Send template messages

    Args:
        template (str): Template key
        chat_id (int): Telegram Chat ID
        username (str): Telegram Username
    """
    logger = logging.getLogger(__name__)

    logger.debug("Sent template %s  to '@%s'", template, username)
    send_message(
        jinja_env.get_template(f"{template}.txt").render(args=args),
        chat_id
    )

def start_cmd(chat_id, username):
    """/start command logic.
    Shows welcome message.
    
    Args:
        chat_id (int): Telegram Chat ID
        username (str): Telegram Username
    """
    logger = logging.getLogger(__name__)

    logger.debug("User '@%s' issued start command", username)
    send_template("start", chat_id, username)

def help_cmd(chat_id, username):
    """/help command logic.
    Shows help message.
    
    Args:
        chat_id (int): Telegram Chat ID
        username (str): Telegram Username
    """
    logger = logging.getLogger(__name__)

    logger.debug("User '@%s' issued help command", username)
    send_template("help", chat_id, username, WEB_DOMAIN)

def verify_cmd(params, chat_id, username):
    """/verify command logic.
    Verifies 6-digit code.

    Args:
        params (str): Parameters after the command
        chat_id (int): Telegram Chat ID
        username (str): Telegram Username
    """
    logger = logging.getLogger(__name__)

    m = re.match(r".*(\d{6})", params)
    if m is None:
        send_template("verify_empty", chat_id, username)
        return
    logger.info("User '@%s' tried to verify code: %s", username, m.group(1))

    db_con = get_db()
    db_cur = db_con.cursor()
    db_res = db_cur.execute("""
        WITH LatestVerification AS (
            SELECT owner_id, verify_date, verify_code, verify_item
            FROM Verifications
            WHERE verified = 0 AND verify_service = 0
            ORDER BY verify_date DESC
        )
        SELECT
            owner_id,
            verify_date,
            CASE
                WHEN verify_code = ? AND verify_item = ?
                THEN 1
                ELSE 0
            END AS verifiable
        FROM LatestVerification
        ORDER BY verifiable DESC;
    """, (m.group(1), username)).fetchone()
    if not db_res or db_res["verifiable"] == 0:
        db_con.close()
        send_template("verify_invalid", chat_id, username)
        logger.info("User '@%s' is not registered or sent an invalid code.", username)
        return

    owner_id = db_res["owner_id"]

    if (
        math.floor(
            (
                datetime.now() -
                datetime.fromisoformat(
                    db_res["verify_date"]
                )
            ).total_seconds() / 60
        ) > 9
    ):
        db_con.close()
        send_template("verify_expired", chat_id, username)
        logger.info("User '@%s'`s verification code has been expired")
        return

    db_cur.execute("""
        UPDATE
            Verifications
        SET
            verified = 1
        WHERE
            verify_code = ? AND
            verify_item = ? AND
            verify_service = 0 AND
            verified = 0;
    """, (m.group(1), username))
    db_con.commit()

    db_res = db_cur.execute("""
        INSERT INTO
            Telegram_Subscribers
        (owner_id, telegram_username, telegram_chat_id)
        VALUES
            (?, ?, ?)
        RETURNING
            telegram_id;
    """, (owner_id, username, chat_id)).fetchone()

    if not db_res:
        db_con.rollback()
        db_con.close()
        logger.error(
            "Couldn't insert a telegram subscription: (%d, %d, %s)",
            owner_id,
            chat_id,
            username
        )

    telegram_id = db_res["telegram_id"]
    db_con.commit()

    db_res = db_cur.execute("""
        UPDATE Students
        SET active_telegram_id = ?
        WHERE id = ?
    """, (telegram_id, owner_id))

    if not db_res.rowcount > 0:
        db_con.rollback()
        db_con.close()
        logger.error(
            "Couldn't update student's active telegram subscription: (%d, %d)",
            owner_id,
            telegram_id
        )

    send_template("verify_success", chat_id, username)
    db_con.commit()
    db_con.close()

def unsubscribe(chat_id, username):
    """Unsubscribes user

    Args:
        chat_id (int): Telegram Chat ID
        username (str): Telegram Username
    """
    logger = logging.getLogger(__name__)
    db_con = get_db()
    db_cur = db_con.cursor()

    db_res = db_cur.execute("""
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
                    ts.telegram_username = ? AND
                    ts.telegram_chat_id = ?
            );
    """, (username, chat_id))

    if not db_res.rowcount > 0:
        db_con.rollback()
        db_con.close()
        send_template("unsubscribe_nosub", chat_id, username, WEB_DOMAIN)
        logger.info("Couldn't unsubscribe for telegram user '@%s'. No subscriptions", username)
        return

    db_con.commit()
    send_template("unsubscribe", chat_id, username)
    logger.info("Telegram user '@%s' unsubscribed", username)

def process_update(u):
    """Process verifications queue

    Args:
        update (dict): Update object
    """
    if u.get("message"):
        if not u["message"]["chat"]["type"] == "private":
            return
        if (
            u["message"].get("text") and
            u["message"].get("entities")
        ):
            inx = None
            for i, e in enumerate(u["message"]["entities"]):
                if (
                    e["type"] == "bot_command" or
                    not e.get("url", "").find("bot_command") == -1
                ):
                    inx = i
            if inx is None:
                return
            m = re.match(r"/(\w+)(.*)", u["message"].get("text", ""))
            if m is None:
                return
            chat_id = u["message"]["chat"]["id"]
            username = u["message"]["chat"]["username"]
            match m.group(1):
                case "start":
                    start_cmd(chat_id, username)
                case "help":
                    help_cmd(chat_id, username)
                case "verify":
                    verify_cmd(m.group(2), chat_id, username)
                case "unsubscribe":
                    unsubscribe(chat_id, username)

def updates_thread():
    # pylint: disable=W3101
    """Telegram Updates Thread"""
    params = {
        "offset": None,
        "timeout": POLLING_TIMEOUT
    }
    logger = logging.getLogger(__name__)
    while True:
        res = requests.get(
            f"https://{BOT_TELEGRAM_HOSTNAME}/bot{BOT_TELEGRAM_API_KEY}/getUpdates",
            params = {k: v for k, v in params.items() if v is not None}
        )
        if res.status_code == 200:
            for u in res.json()["result"]:
                params["offset"] = u["update_id"] + 1
                process_update(u)
        else:
            logger.error("Error while getting updates")
            time.sleep(REQUEST_TIMEOUT)
