import re

import requests
from requests import RequestException

from ..config import BOT_DISCORD_USERNAME, BOT_DISCORD_AVATAR, REQUEST_TIMEOUT


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


def send_content(webhook, *, content, embeds=None):
    """Discord Webhook: send_content
    Sends content with optional embeds

    Args:
        webhook (str): Webhook URL
        content (str): Content
        embeds (list): Discord Embeds List
    """
    if embeds is None:
        embeds = []

    return send_message(webhook, message={
        "username": BOT_DISCORD_USERNAME,
        "avatar_url": BOT_DISCORD_AVATAR,
        "content": content,
        "embeds": embeds,
    })


def send_message(webhook, *, message):
    """Discord Webhook: send_message
    Sends message object

    Args:
        webhook (str): Webhook URL
        message (dict): Message Dictionary

    Returns:
        bool: If it was successful
    """
    if not is_webhook(webhook):
        return False

    res = requests.request(
        "POST",
        webhook,
        json=message,
        timeout=REQUEST_TIMEOUT,
    )

    if not res.status == 204:
        raise RequestException(res.status_code, res.text)

    return res.text
