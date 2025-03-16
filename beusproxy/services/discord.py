import re

from ..config import BOT_DISCORD_USERNAME, BOT_DISCORD_AVATAR
from .httpclient import HTTPClientError


def is_webhook(url):
    """Checks if it is a valid discord webhook URL

    Args:
        url (str): Webhook URL

    Returns:
        bool: If it is valid
    """
    return re.match(
        r"https://discord.com/api/webhooks/\d{19}/[-_a-zA-Z0-9]{68}/?",
        url,
    ) is not None


def send_content(webhook, *, content, embeds=None, httpc):
    """Discord Webhook: send_content
    Sends content with optional embeds

    Args:
        webhook (str): Webhook URL
        content (str): Content
        embeds (list): Discord Embeds List
        httpc (HTTPClient): HTTP Client
    """
    if embeds is None:
        embeds = []

    return send_message(webhook, httpc=httpc, message={
        "username": BOT_DISCORD_USERNAME,
        "avatar_url": BOT_DISCORD_AVATAR,
        "content": content,
        "embeds": embeds,
    })


def send_message(webhook, *, message, httpc):
    """Discord Webhook: send_message
    Sends message object

    Args:
        webhook (str): Webhook URL
        message (dict): Message Dictionary
        httpc (HTTPClient): HTTP Client

    Returns:
        bool: If it was successful
    """
    if not is_webhook(webhook):
        return False

    res = httpc.request(
        "POST",
        webhook,
        json=message
    )

    if not res.status == 204:
        raise HTTPClientError(res.status, httpc.cr_text(res))

    return httpc.cr_text(res)
