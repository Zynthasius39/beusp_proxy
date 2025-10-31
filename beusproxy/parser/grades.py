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
                    "year": int(m.group(1)),
                    "semester": int(m.group(2)),
                }
            )

    return {"entries": grades_ops, "canRequestAll": all_enabled}


def grades2(html):
    """Grade parser

    Args:
        html (str): HTML input from root server

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
    html = re.sub(r"\\([rnt])", "", html)
    html = re.sub(r"\\", "", html)
    soup = BeautifulSoup(html, "html.parser")
    ys_count = 0
    grades_table = {}
    # Find all year & semester headers.
    table_ys = soup.find_all("b", recursive=False)

    # Find and iterate through grade tables by given class name.
    for table_r in soup.find_all("div", class_="table-responsive"):
        # Seperate table for each semester table.
        table = []
        mode = "old"
        for tr in table_r.find_all("tr"):
            row = []
            for td in tr.find_all("td"):
                if not table:
                    row.append(rename_table[td.text.strip()])
                else:
                    row.append(td.text.strip())
            table.append(row)

        m = re.search(
            r"(\d{4})-\d{4} ([12]). (term|semester)", table_ys[ys_count].text.strip()
        )
        ys_cur = f"{m.group(1)}#{m.group(2)}"
        ys_count += 1
        # Checking if SDF3 exists in header row.
        for i in table[0]:
            if i == "act3":
                mode = "oldold"
                break
            elif i == "sem":
                mode = "latest"
                break
        # Iterating through rows while ignoring header and empty last row.
        for i in table[1:-1]:
            # Old grade X/100
            # New grade X/(10/15/50)
            is_old_graded = False
            row_name = ""
            row = {}
            # Iterating through cells with index.
            for inx, j in enumerate(i):
                # Getting scale in given column.
                grade_field = grade_fields[mode].get(table[0][inx])
                # If field exists in scale table
                # and if it is a digit.
                if grade_field is not None and j.isdigit():
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
                if not table[0][inx] == "courseName":
                    j = j.replace(" ", "")
                # Set course key
                if table[0][inx] == "courseCode":
                    row_name = j
                    continue
                if table[0][inx] in digit_fields:
                    # If grade is empty, set it to -1.
                    if j.strip() == "":
                        j = -1
                    # If it is Q, set it to -2.
                    elif j.strip() == "Q":
                        j = -2
                    # Actual Grade parsing
                    elif j.isdigit():
                        # Getting scale in given column.
                        grade_field = grade_fields[mode].get(table[0][inx])
                        # Convert 100-point scale grade to new scale
                        if grade_field is not None and is_old_graded:
                            j = round(int(j) / 100 * grade_field, 2)
                        else:
                            j = int(j)
                    # If cannot be parsed, set it to -3.
                    else:
                        j = -3
                row[table[0][inx]] = j
            # Appending year & semester header.
            row["ys"] = ys_cur
            grades_table[row_name] = row

    return grades_table


# New headers
rename_table = {
    "ABS.": "absents",
    "Dav": "absents",
    "AVG": "sum",
    "ORT": "sum",
    "IGB": "calc",
    "SDF1": "act1",
    "SDF2": "act2",
    "SDF3": "act3",  # Əfsanələrə görə...
    "SEM": "sem",  # Mırtdaşmaq balı
    "TSI": "iw",
    "DVM": "attendance",
    "SSI": "final",
    "ƏI": "addFinal",
    "TI": "reFinal",
    "N": "n",
    "M": "m",
    "L": "l",
    "Course code": "courseCode",
    "Dərs kodu": "courseCode",
    "Course name": "courseName",
    "Dərsin adı": "courseName",
    "ECTS": "ects",
    "AKTS": "ects",
}

# New grade scale
grade_fields = {
    "oldold": {
        "sum": 100,
        "act1": 10,
        "act2": 10,
        "act3": 10,
        "iw": 10,
        "attendance": 10,
        "final": 50,
        "addfinal": 50,
        "refinal": 50,
    },
    "old": {
        "sum": 100,
        "act1": 15,
        "act2": 15,
        "iw": 10,
        "attendance": 10,
        "final": 50,
        "addfinal": 50,
        "refinal": 50,
    },
    "latest": {
        "sum": 100,
        "act1": 10,
        "act2": 10,
        "sem": 20,
        "iw": 10,
        "final": 50,
        "addfinal": 50,
        "refinal": 50,
    },
}

# Inverted headers table
# Used to translate for notifications
rename_table_inv = {
    "absents": "Absents",
    "sum": "Total",
    "act1": "Mid-semester 1",
    "act2": "Mid-semester 2",
    "act3": "Mid-semester 3",
    "sem": "Practice",
    "iw": "Individual Work",
    "attendance": "Attendance",
    "final": "Final",
    "addFinal": "Additional Final",
    "reFinal": "Repeated Final",
    "courseCode": "Course Code",
    "courseName": "Course Name",
    "ects": "ECTS",
}

# Specifying digit fields.
digit_fields = [
    "absents",
    "ects",
    # "l",  # Unknown field
    "m",
    "n",
    *list({k for i in grade_fields.values() for k in i.keys()}),
]
