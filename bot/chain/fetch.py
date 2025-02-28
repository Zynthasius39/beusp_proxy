import beusproxy.services.database as db


def fetch_subs(cconn, mconn):
    """Fetch subscribed students"""
    stud_rows = mconn.execute(
        """
        SELECT
            id,
            student_id,
            password,
            active_telegram_id,
            active_discord_id,
            active_email_id
        FROM Students
        WHERE NOT (
            active_telegram_id IS NULL AND
            active_discord_id IS NULL AND
            active_email_id IS NULL
        );
    """
    ).fetchall()
    cconn.executemany(
        """
        INSERT INTO Student_Subscribers (
            id,
            student_id,
            password,
            active_telegram_id,
            active_discord_id,
            active_email_id
        )
        VALUES (
            ?, ?, ?, ?, ?, ?
        );
    """,
        stud_rows,
    )
    cconn.commit()
    mconn.close()
