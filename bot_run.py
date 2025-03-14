import logging

from beusproxy.services.email import EmailClient
from beusproxy.services.httpclient import HTTPClient
from bot import run_chain

logging.basicConfig(level=logging.DEBUG)
with HTTPClient() as httpc, EmailClient() as emailc:
    run_chain(httpc, emailc)
