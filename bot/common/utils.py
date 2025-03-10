import jsondiff
from jinja2 import Environment, FileSystemLoader


def grade_diff(grades_old, grades):
    """Grades table comparator

    Args:
        grades_old (dict): Old Grades Table
        grades (dict): New Grades Table

    Returns:
        dict: Differences
    """

    # Differentiate grades using jsondiff.
    jdiff = jsondiff.diff(grades_old, grades, syntax="rightonly")
    # Filter out jsondiff symbols.
    return {
        k: v for k, v in jdiff.items() if not isinstance(k, jsondiff.symbols.Symbol)
    }


def report_gen_html(diffs, grades):
    """HTML Report Generator

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table

    Return:
        str: Rendered HTML Output
    """

    divs = []
    for k, v in diffs.items():
        # Sanity check.
        if grades.get(k) is None:
            continue

        # Construct and append a diff div.
        divs.append(
            {
                "courseCode": k,
                "courseName": grades.get(k).get("courseName"),
                "diffs": [f"{kk}: {vv}" for kk, vv in v.items()],
            }
        )
    # Render and return.
    env = Environment(loader=FileSystemLoader("bot/templates"))
    return env.get_template("report.html").render(divs=divs)
