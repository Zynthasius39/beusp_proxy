<p float="left">
  <img src="https://github.com/user-attachments/assets/26f79338-e0f1-452a-bbf7-708bac6e36d0" width="100px" />
  <img src="https://github.com/user-attachments/assets/3e07f85b-7dbd-4181-b2e9-ae61f249006c" />
</p>

## Student Information System
## Tələbə Məlumat Sistemi

### Individual Assignment for Multi Platform Programming

Student Portal API for students of Baku Engineering University. Written in Flask-RESTful, acts as middleman. Parses incoming HTML, JSON responses to more friendly format and provides documentation for it. Includes notifying bot and subscription services.
This API is designed from a student's point of view. Don't expect a fully working model. Last tested on **Feburary 19, 2025**. You can request sha256sums of your desired static content on root server using advanced status endpoint.

**This service comes with absolutely no warranty!**


**I am not responsible for**

 - Misuse of service
 - Consequences of your actions
 - Getting locked out of your account
 - Getting their credentials stolen by malicious servers

![Screenshot 2024-12-17 at 02-12-11 Baku Engineering University TMS_PMS - Rest API](https://github.com/user-attachments/assets/9e4717bd-5796-48bf-a761-72551e109ac9)

## Getting started (docker)
Coming soon...

## Getting started (manual)
- Set-up the proxy server:
```bash
git clone https://github.com/Zynthasius39/beusp_proxy
cd beusp_proxy
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

- Initialize database for the first time:
```bash
rm beusp.db # Remove if exists
sqlite3 beusp.db < beusp_init.sql
```

- Start the proxy server (deployment):
```bash
uwsgi uwsgi.ini
# or
gunicorn

# Tweak configs for your needs:
# uwsgi.ini, gunicorn.conf.py

# Neither uWSGI, nor gunicorn supports Windows. This tutorial is Linux/macOS only.
# If you don't know what you are doing, just use the Docker container. [Not out yet :(]
```
- If you want a development server instead:
```bash
flask --app beusproxy run --debug

# Reloading may or may not work properly.
# To run without reloading:
flask --app beusproxy run --debug --no-reload
```
- Supported Environmental Variables:
```bash
# Application name
APP_NAME="beusproxy"

# SQLite3 Database file
DATABASE="beusp.db"

# Swagger enabled
FLASGGER_ENABLED="true"

# Serve offline responses
TMSAPI_OFFLINE="false"

# Enable debug logging
DEBUG="false"

# Root server URL
ROOT_SERVER="https://my.beu.edu.az"

# Server hostname
API_HOSTNAME="http://localhost:8000"

# Web hostname
WEB_HOSTNAME="https://localhost"
# Serves static content, used in templates

# Timeouts
REQUEST_TIMEOUT=5
POLING_TIMEOUT=30
# Used in root server requests and Telegram updates

# Folders
DEMO_FOLDER="beusproxy/demo"
TEMPLATES_FOLDER="beusproxy/templates"
# Used by template managers and offline serving

# Bot
BOT_ENABLED="true"
# If bot is enabled, all variables below must be set!

# - Telegram
BOT_TELEGRAM_API_KEY="YOUR_TELEGRAM_BOT_API_KEY"
BOT_TELEGRAM_HOSTNAME="api.telegram.com"

# - Email
BOT_EMAIL_PASSWORD=""
BOT_SMTP_HOSTNAME="smtp.gmail.com"

# - Discord
BOT_DISCORD_USERNAME="BeuTMSBot"
BOT_DISCORD_AVATAR="http://localhost/beutmsbot.png"

# Custom email regex
EMAIL_REGEX="long_email_regex"
```
```diff
# Use proper URL in the webserver
src/Api.ts (Line 1)
+ When offline mode is enabled, no request is being made to root server.
- You need to have the proxy server running!
```
