""" DEBUG """
from datetime import datetime
import json

from .utils import grade_diff

def log4grades(sub_id, subs_grades_old, sub_grades):
    """
    Write notes and changes back to db
    High level debugging
    """
    with open("log/grades_history.log", "a", encoding="utf-8") as f:
        text = {
            "old": json.loads(
                dict(subs_grades_old).get(sub_id, '{"isOldGradesNull": true}')
            ),
            "new": sub_grades,
            "diff": (
                grade_diff(
                    json.loads(
                        dict(subs_grades_old).get(sub_id, '{"isOldGradesNullX": true}')
                    ),
                    sub_grades,
                )
                if dict(subs_grades_old).get(sub_id)
                else {"isOldGradesNull": True}
            ),
        }
        f.write(
            f"[{datetime.now().isoformat()}] - Sub {sub_id}: {json.dumps(text["old"])}\n"
        )
        f.write(f"[{datetime.now().isoformat()}] - |    : {json.dumps(text["new"])}\n")
        f.write(f"[{datetime.now().isoformat()}] - |    : {json.dumps(text["diff"])}\n")
