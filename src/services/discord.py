import re
import requests

from config import (
    BOT_DISCORD_USERNAME,
    BOT_DISCORD_AVATAR
)

def is_webhook(url):
    """Checks if it is a valid discord webhook URL

    Args:
        url (str): Webhook URL

    Returns:
        bool: If it is valid
    """
    m = re.match(
        r"https:\/\/discord.com\/api\/webhooks\/(\d{19})\/([-a-zA-Z0-9()@:%_+.~#?&=]*)",
        url
    )
    
    return m is not None



def send_message(webhook, msg = None, embeds = []):
    """Discord Webhook: send_message
    Sends a message with embeds

    Args:
        webhook (str): Webhook URL
        msg (str, optional): Message. Defaults to None.
        embeds (list, optional): List of Embeds. Defaults to [].

    Returns:
        bool: Result
    """
    if not is_webhook(webhook):
        return False

    res = requests.post(
        webhook,
        json = {
            "username": BOT_DISCORD_USERNAME,
            "avatar_url": BOT_DISCORD_AVATAR,
            "content": msg,
            "embeds": embeds
        }
    )
    
    return res.status_code == 204
