from bs4 import BeautifulSoup

from ..common.utils import parse_date


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
        "courseName",
        "courseEducator",
        "credit",
        "hours",
        "limit",
        "atds",
        "absent",
        "absentPercent",
    ]

    attendance = {}
    # Find attendance table by given class name.
    # Iterating through rows while ignoring header and last empty row.
    for tr in soup.find("table", class_="table box").find_all("tr")[1:-1]:
        course_table = {}
        course_name = ""
        # Iterating through cells while ignoring first and last empty cells.
        for i, td in enumerate(tr.find_all("td")[1:-1]):
            match headers[i]:
                case nh if nh in {
                    "absent",
                    "absentPercent",
                    "atds",
                    "hours",
                    "limit",
                }:
                    # Clean and cast to int
                    try:
                        if nh == "absentPercent":
                            # Clean unnecessary characters.
                            val = int(td.text.strip().replace("%", ""))
                        elif nh == "limit":
                            # Cast limit to float
                            val = float(td.text.strip())
                        else:
                            val = int(td.text.strip())
                    except ValueError:
                        val = -1
                case "code":
                    # Store course_name to be used as key.
                    course_name = td.find("a").text.strip().replace(" ", "")
                    continue
                case "courseEducator":
                    # Clean educator name and surname.
                    course_educator_val = td.text.strip().split(" ")
                    val = (
                        f"{course_educator_val[0].lower().capitalize()} "
                        f"{course_educator_val[1].lower().capitalize()}"
                    )
                case _:
                    val = td.text.strip()
            course_table[headers[i]] = val
        attendance[course_name] = course_table

    return attendance


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
        "datetime",
        "present",
        "place",
    ]

    attendance = []
    # Find attendance table with given id.
    # Iterating through rows while ignoring empty and header rows.
    for tr in soup.find("table", id="tblJourn").find_all("tr")[2:]:
        date = None
        course_table = {}
        # Iterating through cells while ignoring first and last ones.
        for i, td in enumerate(tr.find_all("td", recursive=False)[1:-1]):
            match headers[i]:
                case "date":
                    date = td.text.strip()
                    continue
                case "datetime":
                    val = parse_date(f"{date} {td.text.strip()}", "%d-%mT%H:%M")
                case "place":
                    try:
                        val = int(td.text.strip().split(" ")[0])
                    except ValueError:
                        val = -1
                case "present":
                    val = td.text.strip() == "+"
            course_table[headers[i]] = val
        attendance.append(course_table)

    attendance_table = {"entries": attendance}
    # Find all information div tags without recursion.
    info_divs = soup.find_all("div", recursive=False)
    # Cleaning and splitting values.
    course_val = info_divs[0].find("h4").text.replace(" - ", ":").split(":")
    educator_val = info_divs[1].find("b").text.strip().split(" ")
    attendance_table["course_code"] = course_val[0].strip().replace(" ", "")
    attendance_table["course_name"] = course_val[1].strip()
    attendance_table["educator"] = (
        f"{educator_val[0].lower().capitalize()} "
        f"{educator_val[1].lower().capitalize()}"
    )

    return attendance_table
