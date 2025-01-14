<p float="left">
  <img src="https://github.com/user-attachments/assets/26f79338-e0f1-452a-bbf7-708bac6e36d0" width="100px" />
  <img src="https://github.com/user-attachments/assets/3e07f85b-7dbd-4181-b2e9-ae61f249006c" />
</p>

## Student Information System
## Tələbə Məlumat Sistemi

### Individual Assignment for Multi Platform Programming

![Screenshot 2024-12-17 at 02-12-11 Baku Engineering University TMS_PMS - Rest API](https://github.com/user-attachments/assets/f98020bc-3cee-4375-8ab0-ed9b5319cf03)

### This proxy is designed from a student's point of view
Don't expect a fully working model. Endpoints last tested on 16 December 2024 11:58 PM.

SHA256SUM of ```common/general.js``` found in the website:
```1d750059806e36fa731f0b045e2844bf52e150a404ab01ac5224dc7e10bbf040  general.js```

## Getting started
- Set-up the proxy server:
```bash
git clone https://github.com/Zynthasius39/beusp_proxy
cd beusp_proxy
python3 -m venv .venv
#------------------------------------------------------#
source .venv/bin/activate         # Linux / macOS
.venv\Scripts\activate.ps1        # Windows (Powershell)
.venv\bin\activate                # Windows (CMD)
#------------------------------------------------------#
python3 -m pip install -r requirements.txt
```
- Start the proxy server (deployment):
```bash
# Linux/macOS only
uwsgi --http 0.0.0.0:8000 --master -p 4 -w main:app
```
- If you want a development server instead:
```bash
python3 src/main.py
```
- Enable Swagger:
```bash
export SWAGGER_ENABLED=true      # Linux / macOS
$Env:SWAGGER_ENABLED = "true"    # Windows (Powershell)
set SWAGGER_ENABLED=true         # Windows (CMD)
```
- Enable Offline mode:
```bash
export TMSAPI_OFFLINE=true      # Linux / macOS
$Env:TMSAPI_OFFLINE = "true"    # Windows (Powershell)
set TMSAPI_OFFLINE=true         # Windows (CMD)
```
- Enable Debugging:
```bash
export DEBUG=true      # Linux / macOS
$Env:DEBUG = "true"    # Windows (Powershell)
set DEBUG=true         # Windows (CMD)
```
```diff
# Use proper URL in the webserver
/src/Api.ts (Line 1)
+ When offline mode is enabled, no request is being made to root server.
- You need to have the proxy server running!
```
