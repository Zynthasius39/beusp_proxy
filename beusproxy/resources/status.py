import hashlib

from flask import current_app as app
from flask_restful import Resource, abort, reqparse

from ..common.utils import get_db
from ..config import HOST, ROOT, USER_AGENT
from ..context import c
from ..services.httpclient import HTTPClientError

# Files to calculate the sha256 hashsum of.
hash_files = [
    "/index.php",
    "/common/general.js",
    "/dist/js/adminlte.js",
    "/dist/js/demo.js",
    "/dist/js/datepicker-simple.js",
    "/bower_components/jquery/dist/jquery.min.js",
    "/bower_components/bootstrap/dist/js/bootstrap.min.js",
]


class Status(Resource):
    """Root server status."""

    def get(self):
        """
        Status Endpoint
        Returns the status of root server and statistics. \
        Advanced status also retrieves and hashes static files of root \
        server to verify if any modification is present.
        ---
        tags:
          - Operations
        parameters:
        - name: advanced
          in: query
          description: Advanced status
          required: false
          schema:
            type: boolean
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                students_registered:
                                    type: integer
                                    format: int32
                                    example: 2
                                subscriptions:
                                    type: integer
                                    format: int32
                                    example: 5
                                root_server_is_up:
                                    type: boolean
                                    example: true
                                sha256sums:
                                    type: array
                                    items:
                                        type: string
                                        example: 1d750059806e36fa731f0b045e284\
                                        4bf52e150a404ab01ac5224dc7e10bbf040 general.js
                            required:
                             - students_registered
                             - subscriptions
                             - root_server_is_up
            502:
                description: Bad response from root server
        """
        httpc = c.get("httpc")
        rp = reqparse.RequestParser()
        rp.add_argument(
            "advanced",
            type=bool,
            location="args",
        )
        args = rp.parse_args()
        status_table = {}

        with get_db() as db_con:
            db_cur = db_con.cursor()

            # Get students count.
            db_res = db_cur.execute(
                """
                SELECT COUNT(id) AS c FROM Students;
            """
            ).fetchone()
            if db_res:
                status_table["students_registered"] = db_res["c"]

            # Get total subscribers count.
            db_res = db_cur.execute(
                """
                SELECT ts + es + ds as c FROM
                    (SELECT count(telegram_id) as ts FROM Telegram_Subscribers) JOIN
                    (SELECT count(email_id) as es FROM Email_Subscribers) JOIN
                    (SELECT count(discord_id) as ds FROM Discord_Subscribers);
            """
            ).fetchone()
            if db_res:
                status_table["subscriptions"] = db_res["c"]

        try:
            # Check root server status.
            mid_res = httpc.request(
                "GET", ROOT, headers={"Host": HOST, "User-Agent": USER_AGENT}
            )
            status_table["root_server_is_up"] = mid_res.status == 200

            # Advanced status check.
            # Return hashsums of given files.
            async def none():
                return None

            if args.get("advanced"):
                status_table["sha256sums"] = []
                mid_ress = httpc.gather(
                    *[
                        res.text() if res.status == 200 else none()
                        for res in list(
                            res
                            for res in httpc.gather(
                                *[
                                    httpc.request_coro(
                                        "GET",
                                        ROOT + hash_file,
                                        headers={
                                            "Host": HOST,
                                            "User-Agent": USER_AGENT,
                                        },
                                        allow_redirects=False,
                                    )
                                    for hash_file in hash_files
                                ]
                            )
                        )
                    ]
                )
                for inx, mid_res in enumerate(mid_ress):
                    if not mid_res:
                        continue
                    status_table["sha256sums"].append(
                        f"{hashlib.sha256(
                        mid_res.encode("UTF-8")
                        ).hexdigest()} {hash_files[inx].split("/")[-1]}"
                    )
        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        return status_table
