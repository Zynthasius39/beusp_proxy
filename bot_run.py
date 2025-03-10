import logging

from beusproxy.services.httpclient import HTTPClient
from bot import run_chain

logging.basicConfig(level=logging.DEBUG)
with HTTPClient() as httpc:
    run_chain(httpc)
