import logging
import os
import re
import sys
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _arg_error(arg=None, *, help_msg=None):
    """Log error and exit because of missing argument."""
    if arg:
        logger.error("Invalid %s", arg)
    elif help_msg:
        logger.error(help_msg)
    else:
        logger.error("Invalid configuration")
    sys.exit(2)


def _log_config():
    """Debug exported constants."""
    for a in __all__:
        logger.debug("%s: %s", a, getattr(sys.modules[__name__], a))


# App config

APP_NAME = "beusproxy"
DATABASE = "beusp.db"
REQUEST_TIMEOUT = 10
POLLING_TIMEOUT = 30
DEMO_FOLDER = "beusproxy/demo"
TEMPLATES_FOLDER = "beusproxy/templates"

# Root server config

HOST = "my.beu.edu.az"
ROOT = "https://" + HOST + "/"
USER_AGENT = (
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 "
    "like Mac OS X) AppleWebKit/602.1.50 (KHTML, "
    "like Gecko Version/10.0 Mobile/19A346 Safari/602.1"
)

# BeuTMSBot config

BOT_ENABLED = False

# Used by bot to generate
# emails and telegram response
WEB_HOSTNAME = ""
API_HOSTNAME = ""

BOT_EMAIL = ""
BOT_EMAIL_PASSWORD = "asd"
BOT_SMTP_HOSTNAME = "smtp.gmil.com"
BOT_SMTP_IS_SSL = True
# BOT_IMAP_HOSTNAME = "" # Not used
# BOT_POP_HOSTNAME = "" # Not used
BOT_TELEGRAM_API_KEY = ""
BOT_TELEGRAM_HOSTNAME = "api.telgram.org"
BOT_DISCORD_USERNAME = "BeuTMSBot"
BOT_DISCORD_AVATAR = ""

#
# Do not modify below
#

# Not advised to edit, but here you are
EMAIL_REGEX = r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$"

# Getting ENV

FLASGGER_ENABLED = os.getenv("SWAGGER_ENABLED", "false").lower() == "true"

TMSAPI_OFFLINE = os.getenv("TMSAPI_OFFLINE", "false").lower() == "true"

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if os.path.isfile(database := os.getenv("DATABASE", DATABASE)):
    DATABASE = database
else:
    _arg_error("DATABASE")

if not (APP_NAME := os.getenv("APP_NAME", APP_NAME)):
    _arg_error("APP_NAME")

root_server = urlparse(os.getenv("ROOT_SERVER", ROOT))
if root_server.scheme and root_server.netloc:
    parsed_url = root_server.geturl()
    HOST = root_server.netloc
    ROOT = parsed_url if root_server.path else parsed_url + "/"
else:
    _arg_error("ROOT_SERVER")

app_host = urlparse(os.getenv("API_HOSTNAME", API_HOSTNAME))
if app_host.scheme and app_host.netloc:
    parsed_url = app_host.geturl()
    API_HOSTNAME = parsed_url if app_host.path else parsed_url + "/"
else:
    _arg_error("API_HOSTNAME")

web_host = urlparse(os.getenv("WEB_HOSTNAME", WEB_HOSTNAME))
if web_host.scheme and web_host.netloc:
    parsed_url = web_host.geturl()
    WEB_HOSTNAME = parsed_url if web_host.path else parsed_url + "/"
else:
    _arg_error("WEB_HOSTNAME")

if (request_timeout := os.getenv("REQUEST_TIMEOUT", str(REQUEST_TIMEOUT))).isdigit():
    REQUEST_TIMEOUT = int(request_timeout)
else:
    _arg_error(help_msg="REQUEST_TIMEOUT should be a positive number.")

if (polling_timeout := os.getenv("POLLING_TIMEOUT", str(POLLING_TIMEOUT))).isdigit():
    POLLING_TIMEOUT = int(polling_timeout)
else:
    _arg_error(help_msg="POLLING_TIMEOUT should be a positive number.")

if demo_folder := os.getenv("DEMO_FOLDER", DEMO_FOLDER):
    if os.path.isdir(os.path.expanduser(demo_folder)):
        DEMO_FOLDER = demo_folder
    else:
        _arg_error("DEMO_FOLDER")

if templates_folder := os.getenv("TEMPLATES_FOLDER", TEMPLATES_FOLDER):
    if os.path.isdir(os.path.expanduser(templates_folder)):
        TEMPLATES_FOLDER = templates_folder
    else:
        _arg_error("TEMPLATES_FOLDER")

if bot_enabled := os.getenv("BOT_ENABLED", ""):
    if isinstance(bot_enabled, str):
        BOT_ENABLED = bot_enabled == "true"

if BOT_ENABLED:
    DATABASE = os.getenv("BOT_DATABASE", DATABASE)

    BOT_TELEGRAM_API_KEY = os.getenv("BOT_TELEGRAM_API_KEY", BOT_TELEGRAM_API_KEY)

    BOT_TELEGRAM_HOSTNAME = os.getenv("BOT_TELEGRAM_HOSTNAME", BOT_TELEGRAM_HOSTNAME)

    if re.match(EMAIL_REGEX, bot_email := os.getenv("BOT_EMAIL", "")):
        BOT_EMAIL = bot_email
    else:
        _arg_error("BOT_EMAIL")

    if not (BOT_EMAIL_PASSWORD := os.getenv("BOT_EMAIL_PASSWORD", BOT_EMAIL_PASSWORD)):
        _arg_error("BOT_EMAIL_PASSWORD")

    BOT_SMTP_HOSTNAME = os.getenv("BOT_SMTP_HOSTNAME", BOT_SMTP_HOSTNAME)

    if not (
        BOT_DISCORD_USERNAME := os.getenv("BOT_DISCORD_USERNAME", BOT_DISCORD_USERNAME)
    ):
        _arg_error("BOT_DISCORD_USERNAME")

    dc_avatar = urlparse(os.getenv("BOT_DISCORD_AVATAR", BOT_DISCORD_AVATAR))
    if dc_avatar.scheme and dc_avatar.netloc:
        BOT_DISCORD_AVATAR = dc_avatar.geturl()
    else:
        _arg_error("BOT_DISCORD_AVATAR")

# Export config constants

attrs = [*locals()]
__all__ = []
for attr in attrs:
    IS_CONST = True
    for l in attr.replace("_", ""):
        if not l.isupper():
            IS_CONST = False
            break
    if IS_CONST:
        if not BOT_ENABLED and attr.startswith("BOT_"):
            continue
        __all__.append(attr)
