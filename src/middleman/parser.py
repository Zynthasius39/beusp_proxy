import re
import json

from bs4 import BeautifulSoup

def home_parser(text):
    """Homepage parser
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    student_info_table = {}
    # Find main table with given class name.
    for tr in soup.find("table", class_="table").find_all("tr")[1:]:
        cells = tr.find_all("td")
        if cells:
            # Clean the cell, parse field and value.
            field = re.sub(r"\s\s+", " ", cells[0].text.replace(":", "").strip().replace("\n", ""))
            value = cells[-1].text.strip()
            # Clean the advisor.
            if field == "Advisor":
                value_val = value.split(" ")
                value = f"{value_val[0].lower().capitalize()} {value_val[1].lower().capitalize()}"
            # Add the field if it is not empty.
            if not field == "":
                student_info_table[field] = value

    # Find documents table which is the table without any border.
    documents_table = {}
    for tr in soup.find("table", {"border": "0"}).find_all("tr"):
        for link in tr.find_all("a"):
            # Clean the cell, parse field and value.
            field = link.text.strip()
            value = link["href"].strip()
            # Add the field if it is not empty.
            if not field == "":
                documents_table[field] = value

    # Match image id via regex.
    image_url = re.findall(
        r"(?<==)(.*?)(?=&)",
        soup.find("img", class_="img-circle")["src"].strip())[0]

    return {"home":
        {
            "student_info": student_info_table,
            "documents": documents_table, "image": image_url
        }
    }


def grades_parser(text):
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
        else :
            grades_ops.append({
                "year": m.group(1),
                "semester": m.group(2),
            })

    return {"grade_options": grades_ops, "can_request_all": all_enabled}


def faq_parser(text):
    """FAQ parser
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    faq_table = []
    # Find FAQ sitting in ul element with given class name.
    for li in soup.find("ul", class_="timeline").find_all("li"):
        # Append FAQ item and body into a list.
        faq_table.append(
            {
                "item": li.find(class_="timeline-item").text.strip(),
                "body": li.find(class_="timeline-body").text.strip(),
            }
        )

    return {"faq": faq_table}


def announces_parser(text):
    """Announces parser
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    anns_table = []
    # Find announces sitting in div tags
    # through nested div elements
    # without recursion in given order.
    for dev in (
        soup.find("div", class_="box-body")
        .find_all("div", recursive=False)[-1]
        .find_all("div", recursive=False)
    ):
        # Find nested div tags without recursion.
        subdivs = dev.div.find_all("div", recursive=False)
        # Decompose unneeded br tags.
        for br in subdivs[1].find_all("br"):
            br.decompose()
        # Append Announce to anns_table.
        anns_table.append(
            {
                "name": subdivs[0].i.text.strip(),
                "body": subdivs[1].text.strip(),
                "date": subdivs[2].text.strip(),
            }
        )

    return {"announces": anns_table}


def deps_parser(text):
    """Department parser
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # Translate fields.
    text = text.replace("Code of the department", "dep_code")
    text = text.replace("Department name", "dep_name")
    text = text.replace("Department specific course code prefixes", "dep_prefix")

    soup = BeautifulSoup(text, "html.parser")

    # Collect table cells in a list for further processing.
    table = []
    # Find departments table with given class name.
    for tr in soup.find("div", class_="table-responsive").find_all("tr"):
        row = []
        for td in tr.find_all("td")[:-1]:
            # Append striped cells.
            row.append(td.text.strip())
        # Finally append the row to the list.
        table.append(row)

    deps_table = {}
    # Iterating through rows while ignoring header row.
    for i in table[1:]:
        row_name = ""
        row = {}
        # Iterating through cells with index.
        for inx, j in enumerate(i):
            # If it is the number cell, assign it to be row key.
            if table[0][inx] == "№":
                row_name = j
                continue
            row[table[0][inx]] = j
        deps_table[row_name] = row

    return {"deps": deps_table}


def deps2_parser(text):
    """Department parser by department code
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    # Collect table cells in a list for further processing.
    table = []
    # Find department table with given class name.
    for tr in soup.find("table", class_="table box").find_all("tr"):
        row = []
        for td in tr.find_all("td"):
            row.append(td.text.strip())
        table.append(row)

    deps_table = {}
    # Iterating through rows in table while ignoring header row.
    for i in table[1:]:
        row_name = ""
        row = {}
        # Iterating through cells with index.
        for inx, j in enumerate(i):
            # If it is the number cell, assign it to be row key.
            if table[0][inx] == "№":
                row_name = j
                continue
            row[table[0][inx]] = j
        deps_table[row_name] = row

    return {"dep": deps_table}


def grades2_parser(html):
    """Grade parser
    
    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # Needs to be uncomplicated. [too many nested blocks]
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

        m = re.search(r'(\d{4})-\d{4} ([12]). term', table_ys[ys_count].text.strip())
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


def program2_parser(html):
    """Program parser by year & semester

    Args:
        html (str): HTML input

    Returns:
        str: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    # Return if moddesc div doesn't exist
    if not soup.find("div", class_="moddesc"):
        return None

    # Collecting courses for further processing.
    courses = []
    # Iterating through multiple layers of tables, rows, and cells
    # in a very poorly designed table
    # without recursion
    for course in soup.find("table", id="tblMufredatProg").find_all("tr", recursive=False):
        for i in course.find_all("table", class_="table"):
            for j in i.find_all("table", class_="table"):
                table = []
                for tr in j.find_all("tr"):
                    row = []
                    for td in tr.find_all("td"):
                        row.append(td.text.strip())
                    table.append(row)
                courses.append(table)

    course_table = {}
    # Iterating through semesters.
    for isemester, semester in enumerate(courses):
        semester_table = {}
        # Iterating through subjects while ignoring header.
        for subject in semester[1:]:
            row_name = ""
            row = {}
            # Iterating through fields of the subject with index.
            for i, j in enumerate(subject):
                # Skip if empty
                if not semester[0][i].strip() and not j.strip():
                    continue
                # If it is the number cell, assign it to be row key.
                if semester[0][i] == "№":
                    row_name = j
                    continue
                # Translate fields
                if j == "XXX XXX":
                    j = ""
                if "Non-area lective subject" in j:
                    j = "nae"
                elif "Area Elective Course" in j or "Area elective subject" in j:
                    j = "ae"
                elif "Foreign language" in j:
                    j = "nae_language"
                row[semester[0][i]] = j
            semester_table[row_name] = row
        course_table[str(isemester)] = semester_table

    ae = []
    ae_table = {}
    # Find AE tr tags.
    ae_bs = soup.find(
        lambda tag: (
            tag.name == "div" and
            tag.text == " AE - Area Elective Courses")
    ).parent.parent.parent.parent.find_all("tr")

    if ae_bs:
        # Iterating through tr tags while ignoring header and last two empty rows.
        for tr in ae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            ae.append(row)

        # Generate ae_table using collected cells.
        for i, j in enumerate(ae[1:]):
            row_name = ""
            row = {}
            for k, o in enumerate(j):
                if ae[0][k] == "№":
                    row_name = o
                    continue
                row[ae[0][k]] = o
            ae_table[row_name] = row

    nae = []
    nae_table = {}
    # Find NAE tr tags.
    nae_bs = soup.find(
        lambda tag: tag.name == "div" and
        tag.text == " NAE - Non-Area Elective Courses"
    ).parent.parent.parent.parent.find_all("tr")
    if nae_bs:
        # Iterating through tr tags while ignoring header and last two empty rows.
        for tr in nae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            nae.append(row)

        # Generate nae_table using collected cells.
        for i, j in enumerate(nae[1:]):
            row_name = ""
            row = {}
            for k, o in enumerate(j):
                if nae[0][k] == "№":
                    row_name = o
                    continue
                row[nae[0][k]] = o
            nae_table[row_name] = row

    references = []
    reference_table = {}
    # Find References div tag.
    reference_bs = soup.find(
        lambda tag: (
            tag.name == "div" and
            tag.text == " Courses with normal (one-to-one ) reference"
        )
    )
    if reference_bs:
        # Iterating through tr tags while ignoring header and last empty row.
        for tr in reference_bs.parent.parent.parent.parent.find_all("tr")[1:-1]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            references.append(row)

        # Generate reference_table using collected cells.
        for i, j in enumerate(references[1:]):
            row_name = ""
            row = {}
            for k, o in enumerate(j):
                if references[0][k] == "№":
                    row_name = o
                    continue
                row[references[0][k]] = o
            reference_table[row_name] = row

    return {
        "program": course_table,
        "ae": ae_table,
        "nae": nae_table,
        "references": reference_table
    }


def is_expired(html):
    """Check if session is expired

    Args:
        html (str): HTML input

    Returns:
        bool: Whether the session is expired
    """
    # Check if session is expired.
    # When it is, response will consist of this abomination.
    if (
        html == "#!3%6$#@458#!2*/-&2@"
        or not html.find("Daxil ol - Tələbə Məlumat Sistemi") == -1
    ):
        return True
    return False


def msg_parser(html):
    """Message IDs parser

    Args:
        html (str): HTML input

    Returns:
        list: List of message ids
    """
    msg_ids = []
    # Iterating through matches of regex and append it to list.
    # Regex is used to match message ids from html.
    for i in re.findall(r"(?<=onclick=\"ShowReceivedMessage\().*?(?=\))", html):
        msg_ids.append(i)
    return msg_ids


def msg2_parser(text):
    """Message parser

    Args:
        text (str): HTML input

    Returns:
        dict: JSON output
    """
    # Seperate HTML from JSON
    # It is designed to also
    # Why would you even do that?
    soup = BeautifulSoup(json.loads(text)["DATA"], "html.parser")

    msg = {}
    header = soup.find_all("tr")
    body = soup.find("div", class_="mailbox-read-message")

    # If all fields exist, append them to msg.
    if header[0] and header[1] and header[2] and body:
        msg["from"] = re.sub(
            r"\s\s+", " ",
            header[0]
            .find_all("td")[1]
            .text
            .strip()
            .replace("\n", "")
        )
        msg["date"] = re.sub(
            r"\s\s+",
            " ",
            header[1]
            .find_all("td")[1]
            .text
            .strip()
            .replace("\n", "")
        )
        msg["subject"] = re.sub(
            r"\s\s+",
            " ",
            header[2]
            .find_all("td")[1]
            .text
            .strip()
            .replace("\n", "")
        )
        msg["body"] = re.sub(r"\s\s+", " ", body.text.strip())

    return msg


def is_announce(html):
    """Check if page is an announce page

    Args:
        html (str): HTML input

    Returns:
        bool: If it is an announcment
    """
    # Checking for stud_announce string.
    if not html.find("stud_announce") == -1:
        return True
    return False


def is_there_msg(html):
    """Check if there is a message

    Args:
        html (str): HTML input

    Returns:
        bool: Whether there is a message
    """
    soup = BeautifulSoup(html, "html.parser")

    # Checking if span with given attributes exist.
    if soup.find("span", attrs={"style": "color:#1E1E1E ;font-weight:bold"}):
        return True
    return False


def msg_id_parser(html):
    """Message ID parser

    Args:
        html (str): HTML input

    Returns:
        list: List of message ids
    """
    soup = BeautifulSoup(html, "html.parser")

    msg_ids = []
    # Iterating through matches of regex and append it to list.
    # Regex is used to match message ids from html.
    for i in soup.find_all("span", attrs={"style":"color:#1E1E1E ;font-weight:bold"}):
        for k in re.findall(r"(?<=\().*?(?=\))", i.parent.parent.attrs["onclick"]):
            msg_ids.append(k)
    return msg_ids


def transcript_parser(html):
    # pylint: disable=R0915
    """Transcript parser

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    transcript = {}
    # Find extra table by given class name.
    trs = soup.find("table", class_="simple-table").find_all("tr")

    # Strip, clean and append additional datas to transcript dictionary.
    transcript["semesters"] = {}
    transcript["name"] = trs[0].find_all("td")[1].text.strip()
    transcript["faculty"] = trs[0].find_all("td")[3].text.strip()
    transcript["id"] = trs[1].find_all("td")[1].text.strip()
    transcript["program"] = trs[1].find_all("td")[3].text.strip()
    # Should have got the value via regex.
    # Maybe open a issue?
    transcript["level"] = (
        trs[2]
        .find_all("td")[1]
        .text
        .strip()
        .split(" ")[1]
        .replace("(", "")
        .replace(")", "")
        .lower()
        .capitalize()
    )
    transcript["entry_date"] = trs[2].find_all("td")[3].text.strip()
    transcript["graduation_date"] = trs[3].find_all("td")[2].text.strip()

    footer_counter = 0
    current_semester = {}
    current_semester_label = ""
    # Find main transcript table by given class name.
    table = soup.find("table", class_="table").find_all("tr")

    # Iterating through rows while ignoring header row.
    for tr in table[1:]:
        # Find semester cell by its style.
        semester_label = tr.find("td", attrs={
            "style": "font-weight:bold; border:none; "
            "padding-top:10px; padding-bottom:2px"
        })
        if semester_label:
            # Should have got the value via regex.
            # Maybe open a issue?
            semester_val = (
                semester_label
                .text
                .strip()
                .replace("- ", "")
                .replace(".", "")
                .split(" ")
            )
            # Save year & semester to be used as key.
            current_semester_label = f"{semester_val[0]}#{semester_val[2]}"
            current_semester = {}
            current_semester["courses"] = {}
            continue

        #
        # Semester Footer parsing
        #

        # Check if we stepped upon a row with given styles.
        if (
            tr.attrs.get("style") == "font-size:12px; font-weight:bold" or
            tr.attrs.get("style") == "color:Maroon; font-size:12px; font-weight:bold"
        ):
            # Checking if we hit the end of the table.
            if tr.attrs.get("style") == "color:Maroon; font-size:12px; font-weight:bold":
                # Counter to determine the position of total information rows.
                if footer_counter > 0:
                    if footer_counter == 1:
                        transcript["total_earned_ects"] = (
                            tr
                            .find("td")
                            .text
                            .strip()
                            .replace(" ", "")
                            .split(":")[1]
                        )
                        footer_counter += 1
                    elif footer_counter == 2:
                        transcript["total_earned_credits"] = (
                            tr
                            .find("td")
                            .text
                            .strip()
                            .replace(" ", "")
                            .split(":")[1]
                        )
                        footer_counter += 1
                    elif footer_counter == 3:
                        transcript["total_gpa"] = (
                            tr
                            .find("td")
                            .text
                            .strip()
                            .replace(" ", "")
                            .split(":")[1]
                        )
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
                .text
                .replace("\t", "")
                .replace("\xa0", "")
                .replace("\r", "")
                .strip()
                .split("\n")
            ):
                j = i.replace(" ", "").split(":")
                current_semester[j[0].lower()] = j[1]
            # Appending remaining cells.
            current_semester["total_hours"] = tds[2].text.strip()
            current_semester["total_credits"] = tds[3].text.strip()
            current_semester["spa"] = tds[4].text.strip().replace(" ", "").split(":")[1]
            current_semester["gpa"] = tds[5].text.strip().replace(" ", "").split(":")[1]
            transcript["semesters"][current_semester_label] = current_semester
            continue
        tds = tr.find_all("td")
        course_table = {}
        course_table["name"] = tds[1].text.strip()
        course_table["hours"] = tds[2].text.strip()
        course_table["credit"] = tds[3].text.strip()
        course_table["grade"] = tds[4].text.strip()
        course_table["letter_grade"] = tds[5].text.strip()
        course_table["repeat"] = tds[6].text.strip()
        current_semester["courses"][tds[0].text.strip().replace(" ", "")] = course_table

    return {"transcript" : transcript}


def attendance2_parser(html):
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


def attendance3_parser(html):
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


def is_invalid(html):
    """Check if HTML is invalid
    Used before understanding the bad design of student portal

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    if not html.find("<html>") == -1:
        return True
    return False
