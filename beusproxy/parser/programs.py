from bs4 import BeautifulSoup


def program2(html):
    # pylint: disable=R0912
    # pylint: disable=R0914
    # pylint: disable=R0915
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
    for course in soup.find("table", id="tblMufredatProg").find_all(
        "tr", recursive=False
    ):
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
        lambda tag: tag.name == "div"
        and tag.text
        in {"\xa0AE - Area Elective Courses", "\xa0AE - İxtisas seçməli dərslər"}
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
        lambda tag: tag.name == "div"
        and tag.text
        in {
            "\xa0NAE - Non-Area Elective Courses",
            "\xa0NAE - Qeyri ixtisas seçməli dərslər",
        }
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
            tag.name == "div"
            and tag.text == " Courses with normal (one-to-one ) reference"
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
        "references": reference_table,
    }
