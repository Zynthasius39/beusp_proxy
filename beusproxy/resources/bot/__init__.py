from flask import current_app as app
from flask_restful import Resource, abort
from requests import RequestException

from ...config import BOT_EMAIL
from ...context import c
from ...services.telegram import TelegramClient, get_me
from .subscribe import BotSubscribe
from .verify import BotVerify


class Bot(Resource):
    """BeuTMSBot

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Bot Endpoint
        Gets telegram bot and the email used by bot.
        ---
        tags:
          - Bot
        responses:
            200:
                description: Bot status
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                botEmail:
                                    type: string
                                    example: example@std.beu.edu.az
                                botTelegram:
                                    type: string
                                    example: exampleTelegramBot
            404:
                description: Bot is not active
        """
        bot = {}

        if BOT_EMAIL:
            bot["botEmail"] = BOT_EMAIL

        try:
            telegram_bot = get_me()
        except (AssertionError, RequestException) as e:
            app.logger.error(e)
            abort(502, help="Bad response from root server")
            return

        if telegram_bot:
            if telegram_bot["result"].get("username"):
                bot["botTelegram"] = telegram_bot["result"]["username"]

        return bot


__all__ = ["Bot", "BotSubscribe", "BotVerify"]
