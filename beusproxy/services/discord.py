import re

from beusproxy.config import BOT_DISCORD_USERNAME, BOT_DISCORD_AVATAR
from beusproxy.services.httpclient import HTTPClient


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


def send_message(http_client: HTTPClient, webhook, *, msg=None, embeds=None):
    """Discord Webhook: send_message
    Sends a message with embeds

    Args:
        webhook (str): Webhook URL
        msg (str, optional): Message. Defaults to None.
        embeds (list, optional): List of Embeds. Defaults to [].

    Returns:
        bool: Result
    """
    if embeds is None:
        embeds = []

    if not is_webhook(webhook):
        return False

    res = http_client.request(
        "POST",
        webhook,
        json={
            "username": BOT_DISCORD_USERNAME,
            "avatar_url": BOT_DISCORD_AVATAR,
            "content": msg,
            "embeds": embeds,
        },
    )

    return res.status_code == 204
