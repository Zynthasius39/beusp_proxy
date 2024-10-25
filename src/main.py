import json
from session.tms import TMSession
from session.tms import SessionException

session = None
try:
    session = TMSession(220106041, "KWUMADIHIH9uh0")
except SessionException as e:
    print(e.message)

print(session.json())