import os

# App config

APP_NAME = "beusproxy"
DATABASE = "beusp.db"
REQUEST_TIMEOUT = 10
POLLING_TIMEOUT = 30
TEMPLATES_FOLDER = "src/templates"

# Root server config

HOST = "my.beu.edu.az"
ROOT = "https://" + HOST + "/"
USER_AGENT = (
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 "
    "like Mac OS X) AppleWebKit/602.1.50 (KHTML, "
    "like Gecko Version/10.0 Mobile/19A346 Safari/602.1"
)


# BeuTMSBot config

# Used by bot to generate
# emails and telegram response
WEB_DOMAIN = ""
API_DOMAIN = ""
API_OFFLINE_DOMAIN = ""

BOT_EMAIL = ""
BOT_EMAIL_PASSWORD = ""
BOT_SMTP_HOSTNAME = "smtp.gmail.com"
# BOT_IMAP_HOSTNAME = "" # Not used
# BOT_POP_HOSTNAME = "" # Not used
BOT_TELEGRAM_API_KEY = ""
BOT_TELEGRAM_HOSTNAME = "api.telegram.org"

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

API_DOMAIN = os.getenv(
    "API_DOMAIN",
    API_DOMAIN
)

WEB_DOMAIN = os.getenv(
    "WEB_DOMAIN",
    WEB_DOMAIN
)

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
