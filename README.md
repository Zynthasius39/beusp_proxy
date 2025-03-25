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

## Getting started
- Create .env file with your preferences
```bash
vim .env
```

- Generate shared sqlite3 database
```bash
mkdir -p shared
sqlite3 shared/beusp.db < beusp_init.sql
```

## Docker
- Start docker compose and follow logs
```bash
docker-compose up -d && docker-compose logs -f
```

## Podman (2-ways)
- Build images
```bash
podman build beusp -t zynthasius/beusp:alpine
podman build . -f beusproxy.Dockerfile -t zynthasius/beusproxy:alpine
podman build . -f bot.Dockerfile -t zynthasius/beusproxy:alpine
```

### Run containers directly
```bash
podman network create beusp
podman run -d --name hpage_api --network beusp --env-file .env zynthasius/beusproxy:alpine
podman run -d --name hpage_web --network beusp --env-file .env -p 80:80 zynthasius/beusp:alpine
podman run -d --name hpage_bot --network beusp --env-file .env zynthasius/beusproxy:bot-alpine
```

### Install Quadlets
```bash
rsync -rt quadlet/ /etc/containers/systemd
systemctl daemon-reload
systemctl start hpage_bot
```
Starting hpage_bot unit will start other units as well.
Unit dependencies:
Bot -> Web -> Api

## Manual installation
- Set-up the proxy server:
```bash
git clone https://github.com/Zynthasius39/beusp_proxy
cd beusp_proxy
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

- Start the proxy server (deployment):
```bash
uwsgi uwsgi.ini
# or
gunicorn

# Tweak configs for your needs:
# uwsgi.ini, gunicorn.conf.py

# Neither uWSGI, nor gunicorn supports Windows. This tutorial is Linux/macOS only.
# If you don't know what you are doing, just use the Docker container.
```
- If you want a development server instead:
```bash
# Set DEBUG Environmental variable
export DEBUG=true

flask --app beusproxy run --debug

# Reloading doesn't work for
# for bot and telegram processes
```
- Supported Environmental Variables:
```bash
# Application name
APP_NAME=beusproxy

# SQLite3 Database file
DATABASE=shared/beusp.db

# Swagger enabled
FLASGGER_ENABLED=true

# Serve offline responses
TMSAPI_OFFLINE=false

# Enable debug logging
DEBUG=false

# Root server URL
ROOT_SERVER=https://my.beu.edu.az

# Server hostname
API_HOSTNAME=http://localhost:8080/api

# Internal server hostname
API_INTERNAL_HOSTNAME=http://web/api

# Web hostname
WEB_HOSTNAME=http://localhost:8080
# Serves static content, used in templates

# Timeouts
REQUEST_TIMEOUT=5
POLING_TIMEOUT=30
# Used in root server requests and Telegram updates

# Folders
DEMO_FOLDER=beusproxy/demo
TEMPLATES_FOLDER=beusproxy/templates
# Used by template managers and offline serving

# Bot
BOT_ENABLED=true
# If bot is enabled, all variables below must be set!

# - Telegram
BOT_TELEGRAM_API_KEY=YOUR_TELEGRAM_BOT_API_KEY
BOT_TELEGRAM_HOSTNAME=api.telegram.com

# - Email
BOT_EMAIL_PASSWORD=aaaabbbbccccdddd
BOT_SMTP_HOSTNAME=smtp.gmail.com
# For Gmail, you need to use an app password

# - Discord
BOT_DISCORD_USERNAME=BeuTMSBot
BOT_DISCORD_AVATAR=http://localhost:8080/static/beutmsbot.png

# Custom email regex
EMAIL_REGEX="long_email_regex"
```
```diff
- Change API Url in Frontend
beusp/src/utils/Api.ts (Line 1)

+ You can enable CORS on API
beusproxy/__init__.py (Line 43)

- You need to have the proxy server running!

When offline mode is enabled...

- Demo responses needs to be generated with online server first
python3 generate_demo.py -l STUDENT_ID YOUR_PASSWORD beusproxy/demo

+ No request is being made to root server.
```
