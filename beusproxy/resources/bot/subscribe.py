from datetime import datetime
from smtplib import SMTPException

from flask import make_response
from flask_restful import Resource, abort, reqparse

from ...common.utils import get_db, verify_code_gen
from ...context import c
from ...services.discord import is_webhook
from ...services.email import is_email


class BotSubscribe(Resource):
    """BeuTMSBot Subscribe

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Bot Subscribe Endpoint
        Returns subscriptions of given student.
        ---
        tags:
          - Bot
        description: Gets a list of subscriptions for current user.
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                telegram_user_id:
                                    type: integer
                                    format: int64
                                    example: 1220173140
                                discord_webhook_url:
                                    type: string
                                    example: https://discord.com/api/webhooks/...
                                email:
                                    type: string
                                    example: admin@alakx.com
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "StudentID",
            type=str,
            help="Invalid studentid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        with get_db() as db_con:
            db_cur = db_con.cursor()
            db_res = db_cur.execute(
                """
                SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
                FROM Student_Sessions ss
                INNER JOIN Students s
                ON ss.owner_id = s.id
                WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
                LIMIT 1;
            """,
                (args.get("StudentID"), args.get("SessionID")),
            ).fetchone()
            if db_res is None:
                abort(401, help="Session invalid or has expired")

            subscriptions = {}
            owner_id = db_res["owner_id"]

            if db_res is not None:
                if db_res["active_telegram_id"] is not None:
                    db_sub_res = db_cur.execute(
                        """
                        SELECT ts.telegram_user_id FROM Telegram_Subscribers ts
                        INNER JOIN Students s
                        ON ts.telegram_id = s.active_telegram_id
                        WHERE s.id = ?;
                    """,
                        (owner_id,),
                    ).fetchone()
                    if db_sub_res is not None:
                        subscriptions["telegram_user_id"] = db_sub_res[
                            "telegram_user_id"
                        ]
                if db_res["active_discord_id"] is not None:
                    db_sub_res = (
                        db_con.cursor()
                        .execute(
                            """
                        SELECT ds.discord_webhook_url FROM Discord_Subscribers ds
                        INNER JOIN Students s ON ds.discord_id = s.active_discord_id 
                        WHERE s.id = ?;  
                    """,
                            (owner_id,),
                        )
                        .fetchone()
                    )
                    if db_sub_res is not None:
                        subscriptions["discord_webhook_url"] = db_sub_res[
                            "discord_webhook_url"
                        ]
                if db_res["active_email_id"] is not None:
                    db_sub_res = (
                        db_con.cursor()
                        .execute(
                            """
                        SELECT es.email FROM Email_Subscribers es
                        INNER JOIN Students s ON es.email_id = s.active_email_id
                        WHERE s.id = ?;
                    """,
                            (owner_id,),
                        )
                        .fetchone()
                    )
                    if db_sub_res is not None:
                        subscriptions["email"] = db_sub_res["email"]

        return subscriptions

    def put(self):
        """
        Bot Subscribe Endpoint
        Subscribe to Bot.
        ---
        tags:
          - Bot
        description: Subscribes the current user.
        requestBody:
            description: Subscriptions to add.
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            telegram:
                                type: string
                                description: Telegram
                                example: ""
                            discord_webhook_url:
                                type: string
                                description: Discord Webhook
                                example: https://discord.com/api/webhooks/...
                            email:
                                type: string
                                description: E-Mail
                                example: admin@alakx.com
            required: yes
        responses:
            200:
                description: Nothing to do
            201:
                description: Subscribed
            202:
                description: Waiting for verification
                content:
                    application/json:
                        schema:
                            oneOf:
                              - type: object
                                properties:
                                    telegram_code:
                                        type: integer
                                        format: int32
                                        example: 411001
                                required:
                                  - telegram_code
                              - type: object
                                properties:
                                    email_sent:
                                        type: boolean
                                        example: true
                            example:
                                telegram_code: 411001
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "StudentID",
            type=str,
            help="Invalid studentid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "telegram",
            type=str,
        )
        rp.add_argument(
            "discord_webhook_url",
            type=str,
        )
        rp.add_argument(
            "email",
            type=str,
        )
        args = rp.parse_args()

        with get_db() as db_con:
            db_cur = db_con.cursor()
            db_res = db_cur.execute(
                """
                SELECT ss.owner_id
                FROM Student_Sessions ss
                INNER JOIN Students s
                ON ss.owner_id = s.id
                WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
                LIMIT 1;
                """,
                (args.get("StudentID"), args.get("SessionID")),
            ).fetchone()

            if db_res is None:
                abort(401, help="Session invalid or has expired")

            owner_id = db_res["owner_id"]
            if args.get("telegram") is not None:
                db_cur.execute(
                    """
                    UPDATE Verifications
                    SET verified = TRUE
                    WHERE owner_id = ? AND verified = FALSE AND verify_service = 0;
                """,
                    (owner_id,),
                )
                db_con.commit()
                code = verify_code_gen(6)
                db_cur.execute(
                    """
                    INSERT INTO Verifications
                    (owner_id, verify_code, verify_date, verify_service)
                    VALUES(?, ?, ?, 0);
                """,
                    (
                        owner_id,
                        code,
                        datetime.now().isoformat(),
                    ),
                )
                db_con.commit()
                return {"telegram_code": code}, 202
            if args.get("discord_webhook_url") is not None:
                if not is_webhook(args.get("discord_webhook_url")):
                    abort(400, help="Invalid Discord Webhook URL")
                db_sub_res = db_cur.execute(
                    """
                    INSERT INTO Discord_Subscribers(owner_id, discord_webhook_url)
                    VALUES(?, ?)
                    RETURNING discord_id;
                """,
                    (owner_id, args.get("discord_webhook_url")),
                ).fetchone()
                if db_sub_res is None:
                    db_con.rollback()
                    abort(400, help="Unknown error")
                db_con.commit()
                db_cur.execute(
                    """
                    UPDATE Students
                    SET active_discord_id = ?
                    WHERE id = ?;
                """,
                    (db_sub_res["discord_id"], owner_id),
                )
                db_con.commit()
                return make_response("", 201)
            if args.get("email") is not None:
                if not is_email(args.get("email")):
                    abort(400, help="Invalid E-Mail address")
                db_cur.execute(
                    """
                    UPDATE Verifications
                    SET verified = TRUE
                    WHERE owner_id = ? AND verified = FALSE AND verify_service = 1;
                """,
                    (owner_id,),
                )
                db_con.commit()
                code = verify_code_gen(9)
                db_cur.execute(
                    """
                    INSERT INTO Verifications
                    (owner_id, verify_code, verify_item, verify_date, verify_service)
                    VALUES(?, ?, ?, ?, 1);
                """,
                    (owner_id, code, args.get("email"), datetime.now().isoformat()),
                )
                db_con.commit()
                try:
                    c.get("emailc").send_verification(args.get("email"), code)
                except SMTPException:
                    abort(500)
                return {"email_sent": True}, 202

        return make_response("", 200)

    def delete(self):
        """
        Bot Subscribe Endpoint
        Unsubscribe from Bot.
        Removes the subscription reference to unsubscribe.
        Subscription is still stored for future use.
        ---
        tags:
          - Bot
        description: Unsubscribes the current user.
        parameters:
          - name: unsubscribe
            in: body
            required: yes
            description: Subscriptions to cancel.
            schema:
                type: array
                items:
                    type: string
                example:
                  - telegram
                  - discord
                  - email
        responses:
            202:
                description: Nothing to do
            204:
                description: Unsubscribed
            400:
                description: Cannot find the subscription
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "StudentID",
            type=str,
            help="Invalid studentid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "unsubscribe",
            action="append",
            required=True,
        )
        args = rp.parse_args()

        with get_db() as db_con:
            db_cur = db_con.cursor()
            db_res = db_cur.execute(
                """
                SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
                FROM Student_Sessions ss
                INNER JOIN Students s
                ON ss.owner_id = s.id
                WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
                LIMIT 1;
                """,
                (args.get("StudentID"), args.get("SessionID")),
            ).fetchone()

            res = make_response("", 202)

            if db_res is None:
                abort(401, help="Session invalid or has expired")

            owner_id = db_res["owner_id"]
            unsub_list = args.get("unsubscribe")
            # unsub_list = (
            #     request.get_json().get("unsubscribe")
            #     if isinstance(request.get_json(), dict)
            #     else None
            # )
            # if unsub_list is None:
            #     abort(400, help="Missing unsubscribe array")

            if "telegram" in unsub_list and db_res["active_telegram_id"]:
                db_sub_res = db_cur.execute(
                    """
                    UPDATE Students
                    SET active_telegram_id = NULL
                    WHERE id = ?;
                """,
                    (owner_id,),
                )
                if not db_sub_res.rowcount > 0:
                    db_con.rollback()
                    abort(400, help="Couldn't find the subscription")
                db_con.commit()
                res = make_response("", 204)
            if "discord" in unsub_list and db_res["active_discord_id"]:
                db_sub_res = db_cur.execute(
                    """
                    UPDATE Students
                    SET active_discord_id = NULL
                    WHERE id = ?;
                """,
                    (owner_id,),
                )
                if not db_sub_res.rowcount > 0:
                    db_con.rollback()
                    abort(400, help="Couldn't find the subscription")
                db_con.commit()
                res = make_response("", 204)
            if "email" in unsub_list and db_res["active_email_id"]:
                db_sub_res = db_cur.execute(
                    """
                    UPDATE Students
                    SET active_email_id = NULL
                    WHERE id = ?;
                """,
                    (owner_id,),
                )
                if not db_sub_res.rowcount > 0:
                    db_con.rollback()
                    abort(400, help="Couldn't find the subscription")
                db_con.commit()
                res = make_response("", 204)

        if (
            args.get("telegram_user_id") is not None
            or args.get("discord_webhook_url") is not None
            or args.get("email") is not None
        ):
            abort(400, help="Couldn't find the subscription")

        return res
