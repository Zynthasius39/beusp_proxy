import logging
import os

from flasgger import Swagger
from flask import Flask, g
from flask_cors import CORS
from flask_restful import Api

from .config import (APP_NAME, BOT_ENABLED, DEBUG, FLASGGER_ENABLED,
                     TMSAPI_OFFLINE)
from .context import init_context
from .resources import bot as bot_resources

if TMSAPI_OFFLINE:
    from .resources import offline as resources
else:
    from . import resources


def create_app():
    """App Factory"""
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)

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
        resources={r"/*": {"origins": "http://localhost:5173"}},
    )

    api.add_resource(resources.Msg, "/api/resource/msg")
    api.add_resource(resources.Res, "/api/resource/<resource>")
    api.add_resource(resources.GradesAll, "/api/resource/grades/all")
    api.add_resource(resources.GradesLatest, "/api/resource/grades/latest")
    api.add_resource(resources.Grades,
                     "/api/resource/grades/<int:year>/<int:semester>")
    api.add_resource(
        resources.AttendanceByCourse, "/api/resource/attendance/<int:course_code>"
    )
    api.add_resource(
        resources.AttendanceBySemester,
        "/api/resource/attendance/<int:year>/<int:semester>",
    )
    #api.add_resource(resources.Deps, "/api/resource/deps/<dep_code>")
    api.add_resource(resources.Program,
                     "/api/resource/program/<int:code>/<int:year>")
    api.add_resource(resources.Auth, "/api/auth")
    api.add_resource(resources.LogOut, "/api/logout")
    api.add_resource(resources.Verify, "/api/verify")
    api.add_resource(resources.Settings, "/api/settings")
    api.add_resource(resources.StudPhoto, "/api/resource/studphoto")
    api.add_resource(resources.Status, "/api/status")
    api.add_resource(resources.ReadAnnounce, "/api/readAnnounces")

    if BOT_ENABLED:
        api.add_resource(bot_resources.Bot, "/api/bot")
        api.add_resource(bot_resources.BotSubscribe, "/api/bot/subscribe")
        api.add_resource(bot_resources.BotVerify, "/api/bot/verify/<code>")

    return app
