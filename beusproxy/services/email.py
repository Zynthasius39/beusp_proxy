import math
import re
from datetime import datetime
from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from .database import get_db
from ..common.utils import get_logger
from ..config import (
    API_HOSTNAME,
    WEB_HOSTNAME,
    EMAIL_REGEX,
    BOT_EMAIL,
    BOT_EMAIL_PASSWORD,
    BOT_SMTP_HOSTNAME,
    TEMPLATES_FOLDER, APP_NAME,
)

jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_FOLDER))


class EmailClient:
    """EmailClient base class.
    Sending emails.
    """

    def __init__(self, *, is_ssl: Optional[bool] = True):
        self._server: Optional[SMTP] = None

        if is_ssl:
            self._server = SMTP_SSL(BOT_SMTP_HOSTNAME, 465)
        else:
            self._server = SMTP(BOT_SMTP_HOSTNAME)
        self._server.login(BOT_EMAIL, BOT_EMAIL_PASSWORD)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Close the SMTP server"""
        self._server.close()

    def send(self, mime):
        """Sends an email.
        Gets recipient from MIME object.

        Args:
            mime (MIMEBase): Message as MIME
        """
        self._server.sendmail(BOT_EMAIL, mime["To"], mime.as_string())

    def send_verification(self, recipient, code):
        """Sends verification email.

        Args:
            recipient (str): E-Mail address where verification will be sent to
            code (str): 9-digit code
        """
        self.send(
            generate_mime(
                email_to=recipient,
                email_subject=f"[{APP_NAME}] Verification",
                body=jinja_env.get_template("verify.html").render(
                    assets_link=f"{WEB_HOSTNAME}",
                    verify_link=f"{API_HOSTNAME}/bot/verify/{code}",
                    verify_code=code,
                ),
            )
        )


def is_email(email):
    """Check if email syntax is correct

    Args:
        email (str): E-Mail

    Returns:
        bool: If it is a correct email address
    """
    return (
            re.match(EMAIL_REGEX, email) is not None
    )


def generate_mime(*, email_from=BOT_EMAIL, email_to, email_subject, body, body_type="html"):
    """Generates a MIME

    Args:
        email_from (str): From the email
        email_to (str): To the email
        email_subject (str): Subject of E-Mail
        body (str): Body of E-Mail
        body_type (str): Type of body

    Returns:
        MIMEBase: MIME instance
    """
    mime = MIMEMultipart()
    mime["From"] = email_from
    mime["To"] = email_to
    mime["Subject"] = email_subject
    mime.attach(MIMEText(body, body_type))
    return mime


def verify_email(code):
    """Email verification.
    Verifies 9-digit code.

    Args:
        code (str): 9-digit code
    """
    logger = get_logger(__name__)

    with get_db() as db_con:
        db_cur = db_con.cursor()
        db_res = db_cur.execute(
            """
            SELECT
                owner_id,
                verify_date,
                verify_item
            FROM
                Verifications
            WHERE
                verified = FALSE AND
                verify_service = 1 AND
                verify_code = ?
            ORDER BY verify_date DESC;
        """,
            (code,),
        ).fetchone()
        if not db_res:
            return jinja_env.get_template("verify_failed.html").render(
                assets_link=WEB_HOSTNAME
            )

        owner_id = db_res["owner_id"]
        email = db_res["verify_item"]

        if (
                math.floor(
                    (
                            datetime.now() - datetime.fromisoformat(db_res["verify_date"])
                    ).total_seconds()
                    / 60
                )
                > 29
        ):
            logger.info("%s - verification code has been expired", email)
            return jinja_env.get_template("verify_failed.html").render(
                assets_link=WEB_HOSTNAME
            )

        db_res = db_cur.execute(
            """
            UPDATE
                Verifications
            SET
                verified = TRUE
            WHERE
                verify_code = ? AND
                verify_item = ? AND
                verify_service = 1 AND
                verified = FALSE;
        """,
            (code, email),
        )
        db_con.commit()
        if not db_res.rowcount > 0:
            db_con.rollback()
            logger.info("%s - couldn't find the email, even though found a matching code", email)
            return jinja_env.get_template("verify_failed.html").render(
                assets_link=WEB_HOSTNAME
            )

        db_res = db_cur.execute(
            """
            INSERT INTO
                Email_Subscribers
            (owner_id, email)
            VALUES
                (?, ?)
            RETURNING
                email_id;
        """,
            (owner_id, email),
        ).fetchone()

        if not db_res:
            db_con.rollback()
            logger.error("Couldn't insert a email subscription: (%d, %s)", owner_id, email)

        email_id = db_res["email_id"]
        db_con.commit()

        db_res = db_cur.execute(
            """
            UPDATE Students
            SET active_email_id = ?
            WHERE id = ?
        """,
            (email_id, owner_id),
        )

        if not db_res.rowcount > 0:
            db_con.rollback()
            logger.error(
                "Couldn't update student's active email subscription: (%d, %d, %s)",
                owner_id,
                email_id,
                email,
            )

        db_con.commit()

    return jinja_env.get_template("verify_success.html").render(
        assets_link=WEB_HOSTNAME
    )
