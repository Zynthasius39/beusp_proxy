import random

import jsondiff
from jinja2 import Environment, FileSystemLoader

from beusproxy.config import BOT_DISCORD_USERNAME, BOT_DISCORD_AVATAR
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
    return clean_symbol(jsondiff.diff(dic_old, dic, syntax="rightonly"))


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
        "act3",
        "sem",
        "addFinal",
        "attendance",
        "final",
        "iw",
        "reFinal",
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


def report_gen_dcmsg(diffs, grades):
    """Discord Message Report Generator

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table

    Return:
        dict: Rendered Discord Message
    """
    fields = []
    for course in report_gen_list(diffs, grades):
        value = ""
        for k, v in course["diffs"].items():
            value += f"{k}\n"
            # value += f"{k}: {v}\n"
        fields.append(
            {"name": f"{course['courseCode']} - {course['courseName']}", "value": value}
        )
    return {
        "content": None,
        "embeds": [{"color": random_dec_color(minimum=64), "fields": fields}],
        "username": BOT_DISCORD_USERNAME,
        "avatar_url": BOT_DISCORD_AVATAR,
    }


def report_gen_md(diffs, grades, *, telegram=False):
    """Markdown Report Generator

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table
        telegram (bool): Generate for Telegram

    Return:
        str: Rendered Markdown Output
    """
    # Render and return.
    env = Environment(loader=FileSystemLoader("bot/templates"))
    return env.get_template("telegram_report.txt").render(
        courses=report_gen_list(diffs, grades, telegram=telegram)
    )


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

    colors = []
    report = report_gen_list(diffs, grades)
    for i in report:
        r, g, b = random_rgb_color(minimum=64)
        colors.append(
            {
                "fgColor": rgb2hex((r - 64, g - 64, b - 64)),
                "bgColor": rgb2hex((r, g, b)),
                "borderColor": rgb2hex((r, g, b)),
            }
        )

    return env.get_template("report.html").render(divs=report, colors=colors)


def report_gen_list(diffs, grades, *, telegram=False):
    """Dictionary Generator for rendering

    Args:
        diffs (dict): Differences
        grades (dict): Grades Table
        telegram (bool): Escape Telegram Special Chars

    Return:
        dict: Dictionary used in rendering
    """
    courses = []
    for k, v in diffs.items():
        # Sanity check.
        if not grades.get(k):
            continue

        # Construct and append a diff list.
        diffs_dict = {}
        for kk, vv in v.items():
            # Skips boring fields.
            # Maximum attendance point was 10 at the time of writing.
            if vv != -1 and not (kk == "attendance" and vv == 10):
                if vv == -2:
                    vv = "Q"
                if vv == -3:
                    vv = "Err"
                if telegram:
                    if isinstance(vv, str):
                        vv = escape_tg_chars(vv)
                    diffs_dict[escape_tg_chars(rename_table_inv.get(kk, kk))] = vv
                else:
                    diffs_dict[rename_table_inv.get(kk, kk)] = vv
        courses.append(
            {
                "courseCode": escape_tg_chars(k),
                "courseName": (
                    escape_tg_chars(grades[k].get("courseName"))
                    if telegram
                    else grades[k].get("courseName")
                ),
                "diffs": diffs_dict,
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
    special_chars = {
        "_",
        "-",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    }

    for char in special_chars:
        input_str = input_str.replace(char, "\\" + char)

    return input_str


def random_hex_color():
    """Random color generator

    Returns:
        str: HEX Color
    """
    return "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])


def random_rgb_color(*, minimum=0):
    """Random color generator

    Args:
        minimum (int): Color minimum

    Returns:
        tuple: RGB Color
    """
    return (
        random.randint(minimum, 255),
        random.randint(minimum, 255),
        random.randint(minimum, 255),
    )


def random_dec_color(*, minimum=0):
    """Random color generator

    Args:
        minimum (int): Color minimum

    Returns:
        int: Decimal color
    """
    r, g, b = random_rgb_color(minimum=minimum)
    return r * 256**2 + g * 256 + b


def rgb2hex(rgb_color):
    """RGB To HEX

    Args:
        rgb_color (tuple): RGB Color Tuple

    Returns:
        str: HEX color
    """
    return "#" + "".join(f"{i:02x}" for i in rgb_color)
