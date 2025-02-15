from bs4 import BeautifulSoup

from .common import course_code_parser, courses_parser, references_parser


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
    for inx, semester in enumerate(courses):
        course_table[inx + 1] = courses_parser(semester)

    ae_list = []
    # Find AE tr tags.
    if ae_bs := soup.find(
        lambda tag: tag.name == "div"
        and tag.text
        in {"\xa0AE - Area Elective Courses", "\xa0AE - İxtisas seçməli dərslər"}
    ).parent.parent.parent.parent.find_all("tr"):
        ae = []
        # Iterating through tr tags while ignoring header and last two empty rows.
        for tr in ae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            ae.append(row)

        # Generate ae_list using collected cells.
        ae_list = courses_parser(ae)

    nae_list = []
    # Find NAE tr tags.
    if nae_bs := soup.find(
        lambda tag: tag.name == "div"
        and tag.text
        in {
            "\xa0NAE - Non-Area Elective Courses",
            "\xa0NAE - Qeyri ixtisas seçməli dərslər",
        }
    ).parent.parent.parent.parent.find_all("tr"):
        nae = []
        # Iterating through tr tags while ignoring header and last two empty rows.
        for tr in nae_bs[1:-2]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            nae.append(row)

        # Generate nae_list using collected cells.
        nae_list = courses_parser(nae)

    reference_list = []
    # Find References div tag.
    if reference_bs := soup.find(
        lambda tag: (
            tag.name == "div"
            and tag.text == " Courses with normal (one-to-one ) reference"
        )
    ):
        references = []
        # Iterating through tr tags while ignoring header and last empty row.
        for tr in reference_bs.parent.parent.parent.parent.find_all("tr")[1:-1]:
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            references.append(row)

        # Generate reference_list using collected cells.
        reference_list = references_parser(references)

    return {
        "areaCourses": ae_list,
        "nonAreaCourses": nae_list,
        "courses": course_table,
        "courseRefs": reference_list,
    }
