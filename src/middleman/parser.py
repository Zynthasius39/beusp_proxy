from bs4 import BeautifulSoup
import json
import re

def homeParser(text):
    soup = BeautifulSoup(text, "html.parser")

    student_info_table = {}
    for tr in soup.find("table", class_="table").find_all("tr")[1:]:
        cells = tr.find_all("td")
        if cells:
            field = re.sub(r"\s\s+", " ", cells[0].text.replace(":", "").strip().replace("\n", ""))
            value = cells[-1].text.strip()
            if field == "Advisor":
                value_val = value.split(" ")
                value = f"{value_val[0].lower().capitalize()} {value_val[1].lower().capitalize()}"
            if not field == "":
                student_info_table[field] = value

    documents_table = {}
    for tr in soup.find("table", {"border": "0"}).find_all("tr"):
        for link in tr.find_all("a"):
            field = link.text.strip()
            value = link["href"].strip()
            if not field == "":
                documents_table[field] = value

    image_url = re.findall(r"(?<==)(.*?)(?=&)", soup.find("img", class_="img-circle")["src"].strip())[0]

    return {"home": {"student_info": student_info_table, "documents": documents_table, "image": image_url}}


def faqParser(text):
    soup = BeautifulSoup(text, "html.parser")

    faq_table = []
    for li in soup.find("ul", class_="timeline").find_all("li"):
        faq_table.append(
            {
                "item": li.find(class_="timeline-item").text.strip(),
                "body": li.find(class_="timeline-body").text.strip(),
            }
        )
    return {"faq": faq_table}


def announcesParser(text):
    soup = BeautifulSoup(text, "html.parser")

    anns_table = []
    for dev in (
        soup.find("div", class_="box-body")
        .find_all("div", recursive=False)[-1]
        .find_all("div", recursive=False)
    ):
        subdivs = dev.div.find_all("div", recursive=False)
        for br in subdivs[1].find_all("br"):
            br.decompose()
        anns_table.append(
            {
                "name": subdivs[0].i.text.strip(),
                "body": subdivs[1].text.strip(),
                "date": subdivs[2].text.strip(),
            }
        )
    return {"announces": anns_table}


def depsParser(text):
    text = text.replace("Code of the department", "dep_code")
    text = text.replace("Department name", "dep_name")
    text = text.replace("Department specific course code prefixes", "dep_prefix")

    soup = BeautifulSoup(text, "html.parser")

    table = []
    for tr in soup.find("div", class_="table-responsive").find_all("tr"):
        row = []
        for td in tr.find_all("td")[:-1]:
            row.append(td.text.strip())
        table.append(row)

    deps_table = {}
    for i in table[1:]:
        rowName = ""
        row = {}
        for inx, j in enumerate(i):
            if table[0][inx] == "№":
                rowName = j
                continue
            row[table[0][inx]] = j
        deps_table[rowName] = row

    return {"deps": deps_table}


def depsParser2(text):
    soup = BeautifulSoup(text, "html.parser")

    table = []
    for tr in soup.find("table", class_="table box").find_all("tr"):
        row = []
        for td in tr.find_all("td"):
            row.append(td.text.strip())
        table.append(row)

    deps_table = {}
    for i in table[1:]:
        rowName = ""
        row = {}
        for inx, j in enumerate(i):
            if table[0][inx] == "№":
                rowName = j
                continue
            row[table[0][inx]] = j
        deps_table[rowName] = row

    return {"dep": deps_table}


def gradesParser2(html):
    soup = BeautifulSoup(html, "html.parser")

    table = []
    for tr in soup.find("div", class_="table-responsive").find_all("tr"):
        row = []
        for td in tr.find_all("td"):
            row.append(td.text.strip())
        table.append(row)

    grades_table = {}
    for i in table[1:-1]:
        rowName = ""
        row = {}
        for inx, j in enumerate(i[:-1]):
            if not table[0][inx] == "course_name":
                j = j.replace(" ", "")
            if table[0][inx] == "course_code":
                rowName = j
                continue
            row[table[0][inx]] = j
        grades_table[rowName] = row

    return {"grades": grades_table}


def programParser2(html):
    soup = BeautifulSoup(html, "html.parser")

    if not soup.find("div", class_="moddesc"):
        return None

    courses = []
    for inx, course in enumerate(soup.find("table", id="tblMufredatProg").find_all("tr", recursive=False)):
        for i in course.find_all("table", class_="table"):
            for inx, j in enumerate(i.find_all("table", class_="table")):
                table = []
                for tr in j.find_all("tr"):
                    row = []
                    for td in tr.find_all("td"):
                        row.append(td.text.strip())
                    table.append(row)
                courses.append(table)

    course_table = {}
    for isemester, semester in enumerate(courses):
        semester_table = {}
        for isubject, subject in enumerate(semester[1:]):
            rowName = ""
            row = {}
            for i, j in enumerate(subject):
                if not semester[0][i].strip() and not j.strip():
                    continue
                if semester[0][i] == "№":
                    rowName = j
                    continue
                if j == "XXX XXX":
                    j = ""
                if "Non-area lective subject" in j:
                    j = "nae"
                elif "Area Elective Course" in j or "Area elective subject" in j:
                    j = "ae"
                elif "Foreign language" in j:
                    j = "nae_language"
                row[semester[0][i]] = j
            semester_table[rowName] = row
        course_table[str(isemester)] = semester_table

    ae = []
    ae_table = {}
    ae_bs = soup.find(lambda tag: tag.name == "div" and tag.text == " AE - Area Elective Courses").parent.parent.parent.parent.find_all("tr")
    if ae_bs:
        for tr in ae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            ae.append(row)

        for i, j in enumerate(ae[1:]):
            rowName = ""
            row = {}
            for k, o in enumerate(j):
                if ae[0][k] == "№":
                    rowName = o
                    continue
                row[ae[0][k]] = o
            ae_table[rowName] = row

    nae = []
    nae_table = {}
    nae_bs = soup.find(lambda tag: tag.name == "div" and tag.text == " NAE - Non-Area Elective Courses").parent.parent.parent.parent.find_all("tr")
    if nae_bs:
        for tr in nae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            nae.append(row)

        for i, j in enumerate(nae[1:]):
            rowName = ""
            row = {}
            for k, o in enumerate(j):
                if nae[0][k] == "№":
                    rowName = o
                    continue
                row[nae[0][k]] = o
            nae_table[rowName] = row

    references = []
    reference_table = {}
    reference_bs = soup.find(lambda tag: tag.name == "div" and tag.text == " Courses with normal (one-to-one ) reference")
    if reference_bs:
        for tr in reference_bs.parent.parent.parent.parent.find_all("tr")[1:-1]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            references.append(row)

        for i, j in enumerate(references[1:]):
            rowName = ""
            row = {}
            for k, o in enumerate(j):
                if references[0][k] == "№":
                    rowName = o
                    continue
                row[references[0][k]] = o
            reference_table[rowName] = row

    return {
        "program": course_table,
        "ae": ae_table,
        "nae": nae_table,
        "references": reference_table
    }


def isExpired(html):
    if (
        html == "#!3%6$#@458#!2*/-&2@"
        or not html.find("Daxil ol - Tələbə Məlumat Sistemi") == -1
    ):
        return True
    return False


def msgParser(html):
    msg_ids = []
    for i in re.findall(r"(?<=onclick=\"ShowReceivedMessage\().*?(?=\))", html):
        msg_ids.append(i)
    return msg_ids


def msgParser2(text):
    soup = BeautifulSoup(json.loads(text)["DATA"], "html.parser")

    msg = {}
    header = soup.find_all("tr")
    body = soup.find("div", class_="mailbox-read-message")

    if header[0] and header[1] and header[2] and body:
        msg["from"] = re.sub(r"\s\s+", " ", header[0].find_all("td")[1].text.strip().replace("\n", ""))
        msg["date"] = re.sub(r"\s\s+", " ", header[1].find_all("td")[1].text.strip().replace("\n", ""))
        msg["subject"] = re.sub(r"\s\s+", " ", header[2].find_all("td")[1].text.strip().replace("\n", ""))
        msg["body"] = re.sub(r"\s\s+", " ", body.text.strip())

    return msg


def isAnnounce(html):
    if not html.find("stud_announce") == -1:
        return True
    return False


def isThereMsg(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("span", attrs={"style": "color:#1E1E1E ;font-weight:bold"}):
        return True
    return False


def msgIdParser(html):
    soup = BeautifulSoup(html, "html.parser")

    msg_ids = []
    for i in soup.find_all("span", attrs={"style":"color:#1E1E1E ;font-weight:bold"}):
        for k in re.findall(r"(?<=\().*?(?=\))", i.parent.parent.attrs["onclick"]):
            msg_ids.append(k)
    return msg_ids


def transcriptParser(html):
    soup = BeautifulSoup(html, "html.parser")

    transcript = {}
    trs = soup.find("table", class_="simple-table").find_all("tr")
    transcript["name"] = trs[0].find_all("td")[1].text.strip()
    transcript["faculty"] = trs[0].find_all("td")[3].text.strip()
    transcript["id"] = trs[1].find_all("td")[1].text.strip()
    transcript["program"] = trs[1].find_all("td")[3].text.strip()
    transcript["level"] = trs[2].find_all("td")[1].text.strip().split(" ")[1].replace("(", "").replace(")", "").lower().capitalize()
    transcript["entry_date"] = trs[2].find_all("td")[3].text.strip()
    transcript["graduation_date"] = trs[3].find_all("td")[2].text.strip()

    footer_counter = 0
    current_semester = {}
    current_semester_label = ""
    table = soup.find("table", class_="table").find_all("tr")

    for tr in table[1:]:
        semester_label = tr.find("td", attrs={"style": "font-weight:bold; border:none; padding-top:10px; padding-bottom:2px"})
        if semester_label:
            semester_val = semester_label.text.strip().replace("- ", "").replace(".", "").split(" ")
            current_semester_label = f"{semester_val[0]}#{semester_val[2]}"
            current_semester = {}
            current_semester["courses"] = {}
            continue
        if tr.attrs.get("style") == "font-size:12px; font-weight:bold" or tr.attrs.get("style") == "color:Maroon; font-size:12px; font-weight:bold":
            if tr.attrs.get("style") == "color:Maroon; font-size:12px; font-weight:bold":
                if footer_counter > 0:
                    if footer_counter == 1:
                        transcript["total_earned_ects"] = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        footer_counter += 1
                    elif footer_counter == 2:
                        transcript["total_earned_credits"] = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        footer_counter += 1
                    elif footer_counter == 3:
                        transcript["total_gpa"] = tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        footer_counter += 1
                    continue
                footer_counter = 1
            tds = tr.find_all("td")
            for i in tds[1].text.replace(u"\t", "").replace(u"\xa0", u"").replace(u"\r", u"").strip().split(u"\n"):
                j = i.replace(" ", u"").split(":")
                current_semester[j[0].lower()] = j[1]
            current_semester["sac"]
            current_semester["total_hours"] = tds[2].text.strip()
            current_semester["total_credits"] = tds[3].text.strip()
            current_semester["spa"] = tds[4].text.strip().replace(" ", "").split(":")[1]
            current_semester["gpa"] = tds[5].text.strip().replace(" ", "").split(":")[1]
            transcript[current_semester_label] = current_semester
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


def attendanceParser2(html):
    soup = BeautifulSoup(html, "html.parser")

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
    for tr in soup.find("table", class_="table box").find_all("tr")[1:-1]:
        course_table = {}
        course_name = ""
        for i, td in enumerate(tr.find_all("td")[1:-1]):
            val = td.text.strip()
            if i == 0:
                course_name = td.find("a").text.strip().replace(" ", "")
                continue
            elif i == 2:
                course_educator_val = td.text.strip().split(" ")
                val = f"{course_educator_val[0].lower().capitalize()} {course_educator_val[1].lower().capitalize()}"
            elif i == 8:
                val = td.text.strip().replace("%", "")
            course_table[headers[i]] = val
        attendance[course_name] = course_table


    return {"attendance": attendance}


def attendanceParser3(html):
    soup = BeautifulSoup(html, "html.parser")

    headers = [
        "date",
        "hour",
        "present",
        "place",
    ]

    attendance = []
    for tr in soup.find("table", id="tblJourn").find_all("tr")[2:]:
        course_table = {}
        for i, td in enumerate(tr.find_all("td", recursive=False)[1:-1]):
            val = td.text.strip()
            course_table[headers[i]] = val
        attendance.append(course_table)

    attendance_table = {"data": attendance}
    info_divs = soup.find_all("div", recursive=False)
    course_val = info_divs[0].find("h4").text.replace(" - ", ":").split(":")
    educator_val = info_divs[1].find("b").text.strip().split(" ")
    attendance_table["course_code"] = course_val[0].strip()
    attendance_table["course_name"] = course_val[1].strip()
    attendance_table["educator"] = f"{educator_val[0].lower().capitalize()} {educator_val[1].lower().capitalize()}"

    return {"attendance": attendance_table}


def isInvalid(html):
    if not html.find("<html>") == -1:
        return True
    return False
