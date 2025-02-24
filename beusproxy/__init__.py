import logging
import os

from flasgger import Swagger
from flask import Flask, g
from flask import logging as flogging
from flask import make_response, request
from flask_cors import CORS
from flask_restful import Api

from .config import APP_NAME, BOT_ENABLED, FLASGGER_ENABLED, TMSAPI_OFFLINE
from .context import init_context
from .resources import bot as bot_resources
from .services.email import EmailClient
from .services.httpclient import HTTPClient
from .services.telegram import TelegramClient

if TMSAPI_OFFLINE:
    from .resources import offline as resources
else:
    from . import resources


def create_app():
    """App Factory"""
    # logging.basicConfig(level=logging.DEBUG)
    for logger in (APP_NAME, "telegram", "email", "httpclient"):
        logging.getLogger(logger).addHandler(flogging.default_handler)

    curdir = os.path.dirname(os.path.abspath(__file__))

    init_context()

    app = Flask(__name__)

    if FLASGGER_ENABLED:
        app.name = APP_NAME
        Swagger(app=app, template_file=os.path.join(curdir, "swagger.yml"))

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

    api.add_resource(resources.Msg, "/resource/msg")
    api.add_resource(resources.Res, "/resource/<resource>")
    api.add_resource(resources.GradesAll, "/resource/grades/all")
    api.add_resource(resources.Grades, "/resource/grades/<int:year>/<int:semester>")
    api.add_resource(
        resources.AttendanceByCourse, "/resource/attendance/<int:course_code>"
    )
    api.add_resource(
        resources.AttendanceBySemester,
        "/resource/attendance/<int:year>/<int:semester>",
    )
    api.add_resource(resources.Deps, "/resource/deps/<dep_code>")
    api.add_resource(resources.Program, "/resource/program/<int:code>/<int:year>")
    api.add_resource(resources.Auth, "/auth")
    api.add_resource(resources.LogOut, "/logout")
    api.add_resource(resources.Verify, "/verify")
    api.add_resource(resources.Settings, "/settings")
    api.add_resource(resources.StudPhoto, "/resource/studphoto")
    api.add_resource(resources.Status, "/status")
    api.add_resource(resources.ReadAnnounce, "/readAnnounces")

    if BOT_ENABLED:
        api.add_resource(bot_resources.Bot, "/bot")
        api.add_resource(bot_resources.BotSubscribe, "/bot/subscribe")
        api.add_resource(bot_resources.BotVerify, "/bot/verify/<code>")

    return app
