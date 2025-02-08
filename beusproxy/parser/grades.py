import re

from bs4 import BeautifulSoup


def grades(text):
    """Grades parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    grades_ops = []
    all_enabled = False
    # Find all grade options in select tag with given id.
    for op in soup.find("select", id="ysem").find_all("option"):
        # Match year and semester via regex. 2024#2 -> ("2024", "2").
        m = re.search(r"(\d+)#(\d)", op.attrs.get("value"))
        # If year is 1, inform that all grades can be requested at once.
        if m.group(1) == "1":
            all_enabled = True
        # Append year and semester.
        else:
            grades_ops.append(
                {
                    "year": m.group(1),
                    "semester": m.group(2),
                }
            )

    return {"grade_options": grades_ops, "can_request_all": all_enabled}


def grades2(html):
    """Grade parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # Needs to be uncomplicated. [too many nested blocks]
    # PRs are welcomed!
    # pylint: disable=R0914
    # pylint: disable=R0912
    # pylint: disable=R0915
    # pylint: disable=R1702

    # Cleaning input HTML.
    html = re.sub(r"\\(r|n|t)", "", html)
    html = re.sub(r"\\", "", html)
    soup = BeautifulSoup(html, "html.parser")

    # New headers
    rename_table = {
        "ABS.": "absents",
        "AVG": "sum",
        "IGB": "calc",
        "SDF1": "act1",
        "SDF2": "act2",
        "SDF3": "act3",
        "TSI": "iw",
        "DVM": "att",
        "SSI": "final",
        "ƏI": "addfinal",
        "TI": "refinal",
        "N": "n",
        "M": "m",
        "L": "l",
        "Course code": "course_code",
        "Course name": "course_name",
        "ECTS": "ects",
    }

    # New grade scale
    grade_fields = {
        "sum": 100,
        "act1": 15,
        "act2": 15,
        "act3": 10,
        "iw": 10,
        "att": 10,
        "final": 50,
        "addfinal": 50,
        "refinal": 50,
    }

    # Specifing digit fields.
    digit_fields = [
        "absents",
        "ects",
        # "l", Unknown field
        "m",
        "n",
        *grade_fields.keys(),
    ]

    ys_count = 0
    grades_table = {}
    # Find all year & semester headers.
    table_ys = soup.find_all("b", recursive=False)

    # Find and iterate through grade tables by given class name.
    for table_r in soup.find_all("div", class_="table-responsive"):
        # Seperate table for each semester table.
        table = []
        act3_enabled = False
        for tr in table_r.find_all("tr"):
            row = []
            for td in tr.find_all("td"):
                if not table:
                    row.append(rename_table[td.text.strip()])
                else:
                    row.append(td.text.strip())
            table.append(row)

        m = re.search(r"(\d{4})-\d{4} ([12]). term", table_ys[ys_count].text.strip())
        ys_cur = f"{m.group(1)}#{m.group(2)}"
        ys_count += 1
        # Checking if SDF3 exists in header row.
        for i in table[0]:
            if i == "act3":
                act3_enabled = True
                break
        # Iterating through rows while ignoring header and empty last row.
        for i in table[1:-1]:
            is_old_graded = False
            row_name = ""
            row = {}
            # Iterating through cells with index.
            for inx, j in enumerate(i):
                # Getting scale in given column.
                grade_field = grade_fields.get(table[0][inx])
                # If field exists in scale table
                # and if it is a digit.
                if not grade_field is None and j.isdigit():
                    # Cast the grade into int.
                    grade = int(j)
                    # Check if grade table is using old scale.
                    if grade > grade_field:
                        is_old_graded = True
                        break
            # Iterating through cells with index.
            for inx, j in enumerate(i):
                # Skip calculator column.
                if table[0][inx] == "calc":
                    continue
                # Remove whitespace in all cells except course name.
                if not table[0][inx] == "course_name":
                    j = j.replace(" ", "")
                # Set course key
                if table[0][inx] == "course_code":
                    row_name = j
                    continue
                # If grade is empty, set it to -1.
                if table[0][inx] in digit_fields:
                    if j.strip() == "":
                        j = -1
                    else:
                        # Getting scale in given column.
                        grade_field = grade_fields.get(table[0][inx])
                        # Set SDF1 and SDF2 scale to 10, if SDF3 is enabled.
                        if act3_enabled and grade_field == 15:
                            grade_field = 10
                        # Convert 100-point scale grade to new scale
                        if not grade_field is None and is_old_graded:
                            j = round(int(j) / 100 * grade_field, 2)
                        else:
                            j = int(j)
                row[table[0][inx]] = j
            # Appending year & semester header.
            row["ys"] = ys_cur
            grades_table[row_name] = row

    return {"grades": grades_table}
