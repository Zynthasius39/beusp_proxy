import os

from flasgger import Swagger

from controller.api import app

if __name__ == '__main__':
    FLASGGER_ENABLED = os.getenv("SWAGGER_ENABLED", "false").lower() == "true"
    TMSAPI_OFFLINE = os.getenv("TMSAPI_OFFLINE", "false").lower() == "true"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    if FLASGGER_ENABLED:
        app.config["SWAGGER"] = {
            "title": "Baku Engineering University: TMS/PMS - Rest API",
            "uiversion": 3,
        }

        swagger = Swagger(app)

    if TMSAPI_OFFLINE:
        app.run(debug = DEBUG, host="0.0.0.0")
    else:
        app.run(debug = DEBUG, host="0.0.0.0")
