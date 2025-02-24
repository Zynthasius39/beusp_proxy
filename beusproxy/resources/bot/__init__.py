from flask import current_app as app
from flask_restful import Resource, abort

from ...config import BOT_EMAIL
from ...context import c
from ...services.httpclient import HTTPClientError
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
                                bot_email:
                                    type: string
                                    example: example@std.beu.edu.az
                                bot_telegram:
                                    type: string
                                    example: example_telegram_bot
            404:
                description: Bot is not active
        """
        bot = {}

        if BOT_EMAIL:
            bot["bot_email"] = BOT_EMAIL

        try:
            telegram_bot = c.get("tgc").get_me()
        except (AssertionError, HTTPClientError) as e:
            app.logger.error(e)
            abort(502, help="Bad response from root server")

        if telegram_bot:
            if telegram_bot["result"].get("username"):
                bot["bot_telegram"] = telegram_bot["result"]["username"]

        return bot


__all__ = ["Bot", "BotSubscribe", "BotVerify"]
