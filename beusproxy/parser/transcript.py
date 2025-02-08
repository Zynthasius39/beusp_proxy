from bs4 import BeautifulSoup


def transcript(html):
    # pylint: disable=R0915
    """Transcript parser

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    soup = BeautifulSoup(html, "html.parser")

    transcript_table = {}
    # Find extra table by given class name.
    trs = soup.find("table", class_="simple-table").find_all("tr")

    # Strip, clean and append additional datas to transcript dictionary.
    transcript_table["semesters"] = {}
    transcript_table["name"] = trs[0].find_all("td")[1].text.strip()
    transcript_table["faculty"] = trs[0].find_all("td")[3].text.strip()
    transcript_table["id"] = trs[1].find_all("td")[1].text.strip()
    transcript_table["program"] = trs[1].find_all("td")[3].text.strip()
    # Should have got the value via regex.
    # Maybe open a issue?
    transcript_table["level"] = (
        trs[2]
        .find_all("td")[1]
        .text.strip()
        .split(" ")[1]
        .replace("(", "")
        .replace(")", "")
        .lower()
        .capitalize()
    )
    transcript_table["entry_date"] = trs[2].find_all("td")[3].text.strip()
    transcript_table["graduation_date"] = trs[3].find_all("td")[2].text.strip()

    footer_counter = 0
    current_semester = {}
    current_semester_label = ""
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
            # Should have got the value via regex.
            # Maybe open a issue?
            semester_val = (
                semester_label.text.strip()
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
                        transcript_table["total_earned_ects"] = (
                            tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        )
                        footer_counter += 1
                    elif footer_counter == 2:
                        transcript_table["total_earned_credits"] = (
                            tr.find("td").text.strip().replace(" ", "").split(":")[1]
                        )
                        footer_counter += 1
                    elif footer_counter == 3:
                        transcript_table["total_gpa"] = (
                            tr.find("td").text.strip().replace(" ", "").split(":")[1]
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
                .text.replace("\t", "")
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
            transcript_table["semesters"][current_semester_label] = current_semester
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

    return {"transcript": transcript_table}
