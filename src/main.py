import logging
from threading import Thread

from flask.logging import default_handler
from flasgger import Swagger
from werkzeug import serving

from services import telegram

from config import (
    APP_NAME,
    BOT_ENABLED,
    DEBUG,
    FLASGGER_ENABLED,
    TMSAPI_OFFLINE
)

TELEGRAM_THREAD = None

if __name__ == '__main__':
    if TMSAPI_OFFLINE:
        from controller.api_offline import app
    else:
        from controller.api import app

    if FLASGGER_ENABLED:
        app.name = APP_NAME
        app.config["SWAGGER"] = {
            "title": "Baku Engineering University: TMS/PMS - Rest API",
            "uiversion": 3,
        }

        swagger = Swagger(app)

    logging.basicConfig(level=logging.DEBUG)
    for logger in (
        logging.getLogger(app.name),
        logging.getLogger("telegram")
    ):
        logger.addHandler(default_handler)

    if (
        BOT_ENABLED and
        not serving.is_running_from_reloader()
    ):
        TELEGRAM_THREAD = Thread(
            name="telegram_updates",
            target=telegram.updates_thread,
            daemon=True
        )
        TELEGRAM_THREAD.start()

    app.run(debug = DEBUG, host="0.0.0.0")
