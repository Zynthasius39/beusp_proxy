import logging

import jsondiff
from jinja2 import Environment, FileSystemLoader

from beusproxy.parser.grades import rename_table_inv


def diff(dic_old, dic):
    """JSONDiff wrapper

    Args:
        dic_old (dict): Old Dictionary
        dic (dict): New Dictionary

    Returns:
        dict: Differences
    """
    # Filter out jsondiff symbols.
    return clean_symbol(jsondiff.diff(dic_old, dic))


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
                    v.pop(kk)
            if len(v) == 0:
                diff_dic.pop(k)

    return diff_dic


def clean_symbol(table):
    """Remove jsondiff Symbols

    Args:
        table (dict): Input table

    Returns:
        dict: Output table
    """
    out_table = {}
    for k, v in table.items():
        if isinstance(k, jsondiff.symbols.Symbol):
            continue
        if isinstance(v, dict):
            v = clean_symbol(v)
        out_table[k] = v
    return out_table

def report_gen_md(diffs, grades):
    """Markdown Report Generator

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table

    Return:
        str: Rendered Markdown Output
    """
    # Render and return.
    env = Environment(loader=FileSystemLoader("bot/templates"))
    return env.get_template("telegram_report.txt").render(courses=report_gen_list(diffs, grades))

def report_gen_html(diffs, grades):
    """HTML5 Report Generator

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table

    Return:
        str: Rendered HTML Output
    """
    # Render and return.
    env = Environment(loader=FileSystemLoader("bot/templates"))
    return env.get_template("report.html").render(divs=report_gen_list(diffs, grades))

def report_gen_list(diffs, grades):
    """Dictionary Generator for rendering

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table

    Return:
        dict: Dictionary used in rendering
    """
    courses = []
    for k, v in diffs.items():
        # Sanity check.
        if not grades.get(k):
            continue

        # Construct and append a diff div.
        courses.append(
            {
                "courseCode": escape_tg_chars(k),
                "courseName": escape_tg_chars(grades[k].get("courseName")),
                # "diffs": [f"{rename_table_inv.get(kk, f"\_notFound\.{kk}")}: ```{vv}```" for kk, vv in v.items()],
                "diffs": {kk: vv for kk, vv in v.items()},
            }
        )

    return courses

def escape_tg_chars(input_str):
    """Escapes Telegram Special Characters

    Args:
        input_str (str): Input string

    Returns:
        str: Output string
    """
    special_chars = {'_', '-', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'}

    output_str = None
    # for char in special_chars:
    #     # output_str = input_str.replace(char, f"\\{char}")
    #     output_str = input_str.replace(char, "")

    output_str = input_str.replace("-", "")
    return output_str