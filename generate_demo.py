"""
Request Demo Responses to be used
In offline mode, from root server
"""

# TODO: Add to README

import argparse
import json
import logging
import pathlib
from urllib.parse import urlparse

from beusproxy.services.httpclient import HTTPClient

parser = argparse.ArgumentParser()

parser.add_argument("destination", help="Destination Folder")
parser.add_argument("-l", "--student-id", help="StudentID to login as", required=True)
parser.add_argument("-p", "--password", help="Password", required=True)
parser.add_argument("-u", "--url", help="Url", default="http://localhost:5000/")
args = parser.parse_args()

url = ""
api_host = urlparse(args.url)
if api_host.scheme and api_host.netloc:
    parsed_url = api_host.geturl()
    url = parsed_url if api_host.path else parsed_url + "/"

httpc = HTTPClient(trust_env=True, proxy="http://127.0.0.1:8081", ssl=False)

demo_table = {
    "transcript.json": "resource/transcript",
    "announces.json": "resource/announces",
    "attendance2.json": "resource/attendance/58120",
    "attendance3.json": "resource/attendance/2022/2",
    "deps.json": "resource/deps",
    "deps2.json": "resource/deps/DEP_IT_PROG",
    "faq.json": "resource/faq",
    "grades.json": "resource/grades",
    "grades2.json": "resource/grades/2022/2",
    "grades_latest.json": "resource/grades/2024/1",
    "grades_all.json": "resource/grades/all",
    "home.json": "resource/home",
    "msg.json": "resource/msg",
    "program.json": "resource/program/10106/2022",
    "status.json": "status?advanced=1",
}

res = httpc.request(
    "GET",
    f"{url}auth",
    params={
        "studentId": args.student_id,
        "password": args.password
    }
)

assert res.status == 200

session_id = res.cookies.get("SessionID")
student_id = res.cookies.get("StudentID")
dest_path = pathlib.Path(args.destination)

if not dest_path.is_dir():
    logging.error("Invalid destination directory: %s", str(dest_path))

for fn, path in demo_table.items():
    res = httpc.request(
        "GET",
        f"{url}{path}",
        headers={
            "Cookie": f"SessionID={session_id}; StudentID={student_id}",
        }
    )
    if res.status != 200:
        logging.error("Couldn't get response for %s: %d, %s", path, res.status, httpc.cr_text(res))
        continue
    with open(dest_path.joinpath(fn), "w", encoding="UTF-8") as f:
        f.write(json.dumps(httpc.cr_json(res), indent=2, ensure_ascii=False))
