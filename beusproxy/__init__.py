import logging

from flasgger import Swagger
from flask import Flask, jsonify, make_response, logging as flogging, request, g
from flask_restful import Api
from flask_cors import CORS

from beusproxy.controller.api import (
    Msg,
    Res,
    Grades,
    GradesAll,
    AttendanceByCourse,
    AttendanceBySemester,
    Deps,
    Program,
    Auth,
    LogOut,
    Verify,
    StudPhoto,
    Bot,
    BotSubscribe,
    BotVerify,
)
from beusproxy.config import APP_NAME, FLASGGER_ENABLED
from beusproxy.context import tgc, httpc, emailc
from beusproxy.services.telegram import TelegramClient
from beusproxy.services.httpclient import HTTPClient
from beusproxy.services.email import EmailClient

# logging.basicConfig(level=logging.DEBUG)
for logger in (APP_NAME, "telegram", "email", "httpclient"):
    logging.getLogger(logger).addHandler(flogging.default_handler)


def create_app():
    """App Factory"""
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

    api.add_resource(Msg, "/api/resource/msg")
    api.add_resource(Res, "/api/resource/<resource>")
    api.add_resource(GradesAll, "/api/resource/grades/all")
    api.add_resource(Grades, "/api/resource/grades/<int:year>/<int:semester>")
    api.add_resource(AttendanceByCourse, "/api/resource/attendance/<int:course>")
    api.add_resource(
        AttendanceBySemester, "/api/resource/attendance/<int:year>/<int:semester>"
    )
    api.add_resource(Deps, "/api/resource/deps/<code>")
    api.add_resource(Program, "/api/resource/program/<int:code>/<int:year>")
    api.add_resource(Auth, "/api/auth")
    api.add_resource(LogOut, "/api/logout")
    api.add_resource(Verify, "/api/verify")
    api.add_resource(StudPhoto, "/api/studphoto")
    api.add_resource(Bot, "/api/bot")
    api.add_resource(BotSubscribe, "/api/bot/subscribe")
    api.add_resource(BotVerify, "/api/bot/verify/<code>")

    return app
