import jsondiff
from jinja2 import Environment, FileSystemLoader


def diff(dic_old, dic):
    """JSONDiff wrapper

    Args:
        dic_old (dict): Old Dictionary
        dic (dict): New Dictionary

    Returns:
        dict: Differences
    """
    return {
        k: v for k, v in jsondiff.diff(
            dic_old,
            dic,
            syntax="rightonly"
        # Filter out jsondiff symbols.
        ).items() if not isinstance(k, jsondiff.symbols.Symbol)
    }

def grade_diff(grades_old, grades):
    """Grades table comparator

    Args:
        grades_old (dict): Old Grades Table
        grades (dict): New Grades Table

    Returns:
        dict: Differences
    """

    # Differentiate grades using jsondiff.
    diff_dic = diff(grades_old, grades)
    
    # Filter
    filter = {
        "absents",
        "act1",
        "act2",
        "addFinal",
        "attendance",
        "final",
        "iw",
        "reFinal"
    }

    for k, v in dict(diff_dic).items():
        if isinstance(v, dict):
            for kk, vv in dict(v).items():
                if kk not in filter:
                    del v[kk]

    return diff_dic


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
