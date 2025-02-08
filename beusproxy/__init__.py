import logging

from flasgger import Swagger
from flask import Flask, jsonify, make_response, logging as flogging, request, g
from flask_restful import Api
from flask_cors import CORS

from .config import APP_NAME, FLASGGER_ENABLED, TMSAPI_OFFLINE
from .context import init_context
from .services.telegram import TelegramClient
from .services.httpclient import HTTPClient
from .services.email import EmailClient
from .resources import bot as bot_resources

if TMSAPI_OFFLINE:
    from .resources import offline as resources
else:
    from . import resources


def create_app():
    """App Factory"""
    # logging.basicConfig(level=logging.DEBUG)
    for logger in (APP_NAME, "telegram", "email", "httpclient"):
        logging.getLogger(logger).addHandler(flogging.default_handler)

    init_context()

    app = Flask(__name__)

    if FLASGGER_ENABLED:
        app.name = APP_NAME
        app.config["SWAGGER"] = {
            "title": "Baku Engineering University: TMS/PMS - Rest API",
            "uiversion": 3,
        }
        Swagger(app)

    @app.teardown_appcontext
    def close_db(_):
        """Close database connection"""
        db = g.pop("db", None)
        if db is not None:
            db.close()

    api = Api(app)
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": "http://10.0.10.75:5173"}},
    )

    api.add_resource(resources.Msg, "/api/resource/msg")
    api.add_resource(resources.Res, "/api/resource/<resource>")
    api.add_resource(resources.GradesAll, "/api/resource/grades/all")
    api.add_resource(resources.Grades, "/api/resource/grades/<int:year>/<int:semester>")
    api.add_resource(
        resources.AttendanceByCourse, "/api/resource/attendance/<int:course>"
    )
    api.add_resource(
        resources.AttendanceBySemester,
        "/api/resource/attendance/<int:year>/<int:semester>",
    )
    api.add_resource(resources.Deps, "/api/resource/deps/<code>")
    api.add_resource(resources.Program, "/api/resource/program/<int:code>/<int:year>")
    api.add_resource(resources.Auth, "/api/auth")
    api.add_resource(resources.LogOut, "/api/logout")
    api.add_resource(resources.Verify, "/api/verify")
    api.add_resource(resources.StudPhoto, "/api/studphoto")
    api.add_resource(bot_resources.Bot, "/api/bot")
    api.add_resource(bot_resources.BotSubscribe, "/api/bot/subscribe")
    api.add_resource(bot_resources.BotVerify, "/api/bot/verify/<code>")

    return app
