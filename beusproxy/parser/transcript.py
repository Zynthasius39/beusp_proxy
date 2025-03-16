import re

from bs4 import BeautifulSoup

from beusproxy.common.utils import parse_date


def transcript(html):
    # pylint: disable=R0912, R0914, R0915, R1719, R1702
    """Transcript parser

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    transcript_table = {"semesters": {}}
    # Find extra table by given class name.
    trs = soup.find("table", class_="simple-table").find_all("tr")

    # Strip, clean and append additional datas to transcript dictionary.
    transcript_table["fullName"] = trs[0].find_all("td")[1].text.strip()
    transcript_table["faculty"] = trs[0].find_all("td")[3].text.strip()
    transcript_table["graduateDate"] = parse_date(trs[3].find_all("td")[2].text.strip())

    # Cast studentId to int.
    student_id_str = trs[1].find_all("td")[1].text.strip()
    transcript_table["studentId"] = int(
        student_id_str if student_id_str.isdigit() else f"_err.{student_id_str}"
    )

    # Parse entryDate.
    entry_date = parse_date(trs[2].find_all("td")[3].text.strip(), no_format=True)
    transcript_table["entryDate"] = entry_date.isoformat()

    # Construct speciality.
    transcript_table["speciality"] = {}
    if m := re.search(r"(.*) \((EN|AZ)", trs[1].find_all("td")[3].text.strip()):
        transcript_table["speciality"]["program"] = m.group(1)
        transcript_table["speciality"]["lang"] = m.group(2).lower()
        transcript_table["speciality"]["program"] = entry_date.year
    if m := re.search(r"\((.*)\)", trs[2].find_all("td")[1].text.strip()):
        transcript_table["level"] = m.group(1).capitalize()
    else:
        transcript_table["level"] = "_missing"

    footer_counter = 0
    current_semester = {}
    # current_semester_label = ""
    # Find main transcript table by given class name.
    table = soup.find("table", class_="table").find_all("tr")

    # Iterating through rows while ignoring header row.
    for tr in table[1:]:
        # Find semester cell by its style.
        semester_label = tr.find(
            "td",
            attrs={
                "style": "font-weight:bold; border:none; "
                         "padding-top:10px; padding-bottom:2px"
            },
        )
        if semester_label:
            # Dictionary creation per year & semester.
            if m := re.search(r"(\d{4}) - \d{4}. ([12])", semester_label.text.strip()):
                if not transcript_table["semesters"].get(m.group(1)):
                    transcript_table["semesters"][m.group(1)] = {}
                transcript_table["semesters"][m.group(1)][m.group(2)] = {"courses": {}}
                current_semester = transcript_table["semesters"][m.group(1)][m.group(2)]
            continue

        #
        # Semester Footer parsing
        #

        # Check if we stepped upon a row with given styles.
        if (
                tr.attrs.get("style") == "font-size:12px; font-weight:bold"
                or tr.attrs.get("style") == "color:Maroon; font-size:12px; font-weight:bold"
        ):
            # Checking if we hit the end of the table.
            if (
                    tr.attrs.get("style")
                    == "color:Maroon; font-size:12px; font-weight:bold"
            ):
                # Counter to determine the position of total information rows.
                if footer_counter > 0:
                    if footer_counter == 1:
                        total_ects = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        try:
                            transcript_table["totalEarnedEcts"] = int(total_ects)
                        except ValueError:
                            transcript_table["totalEarnedEcts"] = f"_err.{total_ects}"
                    elif footer_counter == 2:
                        total_credits = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        try:
                            transcript_table["totalEarnedCredits"] = int(total_credits)
                        except ValueError:
                            transcript_table["totalEarnedCredits"] = f"_err.{total_credits}"
                    elif footer_counter == 3:
                        total_gpa = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        try:
                            transcript_table["totalGpa"] = float(total_gpa)
                        except ValueError:
                            transcript_table["totalGpa"] = f"_err.{total_gpa}"
                    footer_counter += 1
                    continue
                footer_counter = 1

            #
            # Last Semester Footer parsing
            #

            tds = tr.find_all("td")
            # Splitting as first cell contains multiple values.
            # sac, tacc, tatc.
            for i in (
                tds[1]
                    .text.replace("\t", "")
                    .replace("\xa0", "")
                    .replace("\r", "")
                    .strip()
                    .split("\n")
            ):
                j, k = i.replace(" ", "").split(":")
                j, k = j.strip().lower(), k.strip()
                if k == "0t":
                    k = "0"
                current_semester[fields_table.get(j, f"_unk.{j}")] = int(k) if k.isdigit() else f"_err.{k}"
            # Appending remaining cells.
            if (total_hours := tds[2].text.strip()).isdigit():
                current_semester["totalHours"] = int(total_hours)
            else:
                current_semester["totalHours"] = f"_err.{total_hours}"
            if (total_credits := tds[3].text.strip()).isdigit():
                current_semester["totalCredits"] = int(total_credits)
            else:
                current_semester["totalCredits"] = f"_err.{total_credits}"
            spa = tds[4].text.strip().replace(" ", "").split(":")[1]
            try:
                current_semester["spa"] = float(spa)
            except ValueError:
                current_semester["spa"] = f"_err.{spa}"
            gpa = tds[5].text.strip().replace(" ", "").split(":")[1]
            try:
                current_semester["gpa"] = float(gpa)
            except ValueError:
                current_semester["gpa"] = f"_err.{gpa}"
            continue
        tds = tr.find_all("td")
        hours_str = tds[2].text.strip()
        credit_str = tds[3].text.strip()
        grade_str = tds[4].text.strip()

        # Never seen other states of 'repeat'
        course_table = {
            "courseName": tds[1].text.strip(),
            "hours": int(hours_str if hours_str.isdigit() else f"_err.{hours_str}"),
            "courses": int(credit_str if credit_str.isdigit() else f"_err.{credit_str}"),
            "grade": int(grade_str if grade_str.isdigit() else f"_err.{grade_str}"),
            "gradeLetter": tds[5].text.strip(), "repeat": True if tds[6].text.strip() else False
        }
        current_semester["courses"][tds[0].text.strip().replace(" ", "")] = course_table

    return transcript_table

# New headers table
fields_table = {
    "sqk": "sac",
    "tak": "tacc",
    "tqk": "tatc",
    "sac": "sac",
    "tacc": "tacc",
    "tatc": "tatc",
}