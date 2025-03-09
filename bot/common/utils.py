import json

import jsondiff
from jinja2 import Environment, FileSystemLoader


def grade_diff(grades_old, grades):
    """Grades table comparator"""

    jdiff = jsondiff.diff(grades_old, grades, syntax="rightonly")
    return {
        k: v for k, v in jdiff.items() if not isinstance(k, jsondiff.symbols.Symbol)
    }


def notify_parser(sub_id, diffs):
    """Notification Parser"""
    # Get sub services, destinations (sub_id)
    # Parse diffs per service
    # Return notification list


def report_gen_html(diffs, grades):
    """HTML Report Generator"""

    divs = []
    for k, v in diffs.items():
        if grades.get(k) is None:
            continue
        divs.append(
            {
                "courseCode": k,
                "courseName": grades.get(k).get("courseName"),
                "diffs": [f"{kk}: {vv}" for kk, vv in v.items()],
            }
        )
    env = Environment(loader=FileSystemLoader("bot/templates"))
    return env.get_template("report.html").render(divs=divs)
