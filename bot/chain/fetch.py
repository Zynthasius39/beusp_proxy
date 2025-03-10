def fetch_subs(cconn, mconn):
    """Fetch subscribed students

    Args:
        cconn (sqlite3.Connection): CacheDB Connection
        mconn (sqlite3.Connection): MainDB Connection
    """
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
    cconn.execute(
        """
        DELETE FROM Student_Subscribers;
    """
    )
    cconn.executemany(
        """
        INSERT INTO Student_Subscribers (
            sub_id,
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
