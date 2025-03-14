import atexit
import logging
import sys
from smtplib import SMTPAuthenticationError

from jinja2 import Environment, FileSystemLoader

from .config import BOT_ENABLED, TEMPLATES_FOLDER
from .services.email import EmailClient
from .services.httpclient import HTTPClient
from .services.telegram_proc import TelegramProc


class Context:
    """Global context"""

    def __init__(self):
        self._g = {}

    def set(self, key, value):
        """Set a reference"""
        self._g[key] = value

    def get(self, key):
        """Get a reference"""
        return self._g.get(key, None)

    def exists(self, key):
        """Check if reference exists"""
        return key in self._g


c = Context()


def init_context():
    """Initialize the global context"""
    logger = logging.getLogger(__name__)

    try:
        c.set("jinjaenv", Environment(loader=FileSystemLoader(TEMPLATES_FOLDER)))
        c.set("httpc", HTTPClient(trust_env=True))
        if BOT_ENABLED:
            c.set("tgproc", TelegramProc())
            c.set("emailc", EmailClient())
    except SMTPAuthenticationError as e:
        logger.error(e)
        sys.exit(1)

    c.get("jinjaenv").list_templates()

    @atexit.register
    def cleanup():
        """Cleanup resources"""
        if BOT_ENABLED:
            c.get("tgproc").close()
            c.get("emailc").close()
        c.get("httpc").close()
