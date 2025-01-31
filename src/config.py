import os

# Flask config

APP_NAME = "beusproxy"
REQUEST_TIMEOUT = 10
POLLING_TIMEOUT = 30

# Root server config

HOST = "my.beu.edu.az"
ROOT = "https://" + HOST + "/"
USER_AGENT = (
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 "
    "like Mac OS X) AppleWebKit/602.1.50 (KHTML, "
    "like Gecko Version/10.0 Mobile/19A346 Safari/602.1"
)

# SQLITE3 config

DATABASE = "beusp.db"

# BeuTMSBot config

BOT_EMAIL = ""
BOT_EMAIL_PASSWORD = ""
BOT_SMTP_HOSTNAME = ""
# BOT_IMAP_HOSTNAME = "" # Not used
# BOT_POP_HOSTNAME = "" # Not used
BOT_TELEGRAM_API_KEY = ""
BOT_TELEGRAM_HOSTNAME = "api.telegram.org"

BOT_TELEGRAM_TEMPLATES = {
    "start" : """
    Welcome to 🤖 𝐁𝐞𝐮𝐓𝐌𝐒𝐁𝐨𝐭 🤖
    You can subscribe using Telegram
    to get notified about student portal.
    Use /help to get started.
    """,
    "help" : """
    I can help you managing your subscription, go to tms.beu.alakx.com to register before trying to verify.

    Verify your subscription by providing 6-digit code
    /verify XXXXXX

    Unsubscribe all students connected to you Telegram
    /unsubscribe
    """,
    "verify_success": """
    Verification successful! You will now receive updates from student portal.
    """,
    "verify_invalid": """
    Wrong verification code has been provided, or you are not registered yet.
    """,
    "verify_expired": """
    Verification code has already expired. Please generated a new one
    """,
    "verify_notexist": """
    No waiting verifications found on your Telegram. Register on: tms.beu.alakx.com
    """,
    "verify_empty": """
    You haven't provided a verification code.
    """,
    "unsubscribe": """
    Unsubscribed all students connected to your Telegram. You will not receive any updates from student portal.
    """,
    "unsubscribe_nosub": """
    There is not students subscribed on this Telegram. Maybe consider subscribing ? tms.beu.alakx.com
    """
}

BOT_VERIFY_TTL = 60
BOT_VPOOL_CLEAN_TIME = 10

#
# Getting ENV
#

APP_NAME = os.getenv(
    "APP_NAME",
    APP_NAME
)

FLASGGER_ENABLED = os.getenv(
    "SWAGGER_ENABLED",
    "false"
).lower() == "true"

TMSAPI_OFFLINE = os.getenv(
    "TMSAPI_OFFLINE",
    "false"
).lower() == "true"

DEBUG = os.getenv(
    "DEBUG",
    "false"
).lower() == "true"

BOT_ENABLED = os.getenv(
    "BOT_ENABLED",
    "false"
).lower() == "true"

if BOT_ENABLED:
    BOT_TELEGRAM_API_KEY = os.getenv(
        "BOT_TELEGRAM_API_KEY",
        BOT_TELEGRAM_API_KEY
    )

    BOT_EMAIL = os.getenv(
        "BOT_EMAIL",
        BOT_EMAIL
    )

    BOT_EMAIL_PASSWORD = os.getenv(
        "BOT_EMAIL_PASSWORD",
        BOT_EMAIL_PASSWORD
    )

    BOT_SMTP_HOSTNAME = os.getenv(
        "BOT_SMTP_HOSTNAME",
        BOT_SMTP_HOSTNAME
    )
