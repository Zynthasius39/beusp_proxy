import atexit
import logging
import sys
from smtplib import SMTPAuthenticationError

from jinja2 import Environment, FileSystemLoader

from config import TEMPLATES_FOLDER
from services.email import EmailClient
from services.httpclient import HTTPClient
from services.telegram import TelegramClient

jinjaenv = Environment(loader=FileSystemLoader(TEMPLATES_FOLDER))

jinjaenv.list_templates()

logger = logging.getLogger(__name__)

try:
    emailc = EmailClient()
    httpc = HTTPClient(trust_env=True)
    tgc = TelegramClient(httpc, jinjaenv)
except SMTPAuthenticationError as e:
    logger.error(e)
    sys.exit(1)

@atexit.register
def cleanup():
    """Cleanup resources"""
    tgc.close()
    emailc.close()
    httpc.close()
