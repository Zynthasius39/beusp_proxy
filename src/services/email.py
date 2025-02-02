import logging
import math
import re
from datetime import datetime
from smtplib import SMTP, SMTP_SSL, SMTPException, SMTPSenderRefused
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

from services.database import get_db
from config import (
    API_HOSTNAME,
    WEB_HOSTNAME,
    BOT_EMAIL,
    BOT_EMAIL_PASSWORD,
    BOT_SMTP_HOSTNAME,
    TEMPLATES_FOLDER
)

jinja_env = Environment(
    loader = FileSystemLoader(TEMPLATES_FOLDER)
)

def is_email(email):
    """Check if email syntax is correct

    Args:
        email (str): E-Mail
    
    Returns:
        bool: If it is a correct email address
    """
    m = re.match(
        r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$",
        email
    )

    return m is not None

def send_verification(email, code):
    """Sends verification email

    Args:
        email (str): Verification receiving email address
        code (str): 9-digit code
    """
    if not is_email(email):
        raise SMTPSenderRefused

    send_email(
        email,
        generate_mime(
            BOT_EMAIL,
            email,
            jinja_env
                .get_template("email_subject.txt")
                .render(),
            jinja_env
                .get_template("verify.html")
                .render(
                    assets_link = f"{WEB_HOSTNAME}",
                    verify_link = f"{API_HOSTNAME}/bot/verify/{code}",
                    verify_code = code
                ),
            "html"
        )
    )

def get_smtp_server(hostname, is_ssl):
    """Creates a SMTP Server

    Args:
        hostname (str): Hostname to connect
        is_ssl (bool): If SSL is desired

    Returns:
        SMTP: STMP instance
    """
    if is_ssl:
        return SMTP_SSL(hostname, 465)
    return SMTP(hostname)

def generate_mime(email_from, email_to, email_subject, body, body_type):
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

def send_email(email_to, mime):
    """Sends an email

    Args:
        email_to (str): Send to the email
        mime (MIMEBase): Message as MIME

    Returns:
        bool: If the process was successful
    """
    try:
        with get_smtp_server(BOT_SMTP_HOSTNAME, True) as server:
            server.login(BOT_EMAIL, BOT_EMAIL_PASSWORD)
            server.sendmail(BOT_EMAIL, email_to, mime.as_string())
            return True
    except SMTPException:
        return False

def verify_email(code):
    """Email verification.
    Verifies 9-digit code.
    
    Args:
        code (str): 9-digit code
    """
    logger = logging.getLogger(__name__)

    db_con = get_db()
    db_cur = db_con.cursor()
    db_res = db_cur.execute("""
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
    """, (code, )).fetchone()
    if not db_res:
        db_con.close()
        return (
            jinja_env
            .get_template("verify_failed.html")
            .render(assets_link = WEB_HOSTNAME)
        )

    owner_id = db_res["owner_id"]
    email = db_res["verify_item"]

    if (
        math.floor(
            (
                datetime.now() -
                datetime.fromisoformat(
                    db_res["verify_date"]
                )
            ).total_seconds() / 60
        ) > 29
    ):
        db_con.close()
        logger.info("%s - verification code has been expired", email)
        return (
            jinja_env
            .get_template("verify_failed.html")
            .render(assets_link = WEB_HOSTNAME)
        )

    db_cur.execute("""
        UPDATE
            Verifications
        SET
            verified = 1
        WHERE
            verify_code = ? AND
            verify_item = ? AND
            verify_service = 1 AND
            verified = 0;
    """, (code, email))
    db_con.commit()

    db_res = db_cur.execute("""
        INSERT INTO
            Email_Subscribers
        (owner_id, email)
        VALUES
            (?, ?)
        RETURNING
            email_id;
    """, (owner_id, email)).fetchone()

    if not db_res:
        db_con.rollback()
        db_con.close()
        logger.error(
            "Couldn't insert a email subscription: (%d, %s)",
            owner_id,
            email
        )

    email_id = db_res["email_id"]
    db_con.commit()

    db_res = db_cur.execute("""
        UPDATE Students
        SET active_email_id = ?
        WHERE id = ?
    """, (email_id, owner_id))

    if not db_res.rowcount > 0:
        db_con.rollback()
        db_con.close()
        logger.error(
            "Couldn't update student's active email subscription: (%d, %d, %s)",
            owner_id,
            email_id,
            email
        )

    db_con.commit()
    db_con.close()
    return (
        jinja_env
        .get_template("verify_success.html")
        .render(assets_link = WEB_HOSTNAME)
    )
