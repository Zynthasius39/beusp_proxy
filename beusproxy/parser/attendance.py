from bs4 import BeautifulSoup


def attendance2(html):
    """Attendace parser by year & semester

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    # New headers
    headers = [
        "code",
        "course_name",
        "course_educator",
        "credit",
        "hours",
        "limit",
        "atds",
        "absent",
        "absent_percent",
    ]

    attendance = {}
    # Find attendance table by given class name.
    # Iterating through rows while ignoring header and last empty row.
    for tr in soup.find("table", class_="table box").find_all("tr")[1:-1]:
        course_table = {}
        course_name = ""
        # Iterating through cells while ignoring first and last empty cells.
        for i, td in enumerate(tr.find_all("td")[1:-1]):
            val = td.text.strip()
            if i == 0:
                # Store course_name to be used as key.
                course_name = td.find("a").text.strip().replace(" ", "")
                continue
            if i == 2:
                # Clean educator name and surname.
                course_educator_val = td.text.strip().split(" ")
                val = (
                    f"{course_educator_val[0].lower().capitalize()} "
                    f"{course_educator_val[1].lower().capitalize()}"
                )
            elif i == 8:
                # Clean unnecessary characters.
                val = td.text.strip().replace("%", "")
            course_table[headers[i]] = val
        attendance[course_name] = course_table

    return {"attendance": attendance}


def attendance3(html):
    """Attendance parser by course

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    headers = [
        "date",
        "hour",
        "present",
        "place",
    ]

    attendance = []
    # Find attendance table with given id.
    # Iterating through rows while ignoring empty and header rows.
    for tr in soup.find("table", id="tblJourn").find_all("tr")[2:]:
        course_table = {}
        # Iterating through cells while ignoring first and last ones.
        for i, td in enumerate(tr.find_all("td", recursive=False)[1:-1]):
            val = td.text.strip()
            course_table[headers[i]] = val
        attendance.append(course_table)

    attendance_table = {"data": attendance}
    # Find all information div tags without recursion.
    info_divs = soup.find_all("div", recursive=False)
    # Cleaning and splitting values.
    course_val = info_divs[0].find("h4").text.replace(" - ", ":").split(":")
    educator_val = info_divs[1].find("b").text.strip().split(" ")
    attendance_table["course_code"] = course_val[0].strip()
    attendance_table["course_name"] = course_val[1].strip()
    attendance_table["educator"] = (
        f"{educator_val[0].lower().capitalize()} "
        f"{educator_val[1].lower().capitalize()}"
    )

    return {"attendance": attendance_table}
