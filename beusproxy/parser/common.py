import re


def course_code_parser(code):
    """Course Code Parser

    Args:
        code (str): courseCode

    Returns:
        (str): Parsed courseCode
    """
    if nm := re.search(r"(\w+) (\d+)", code):
        return f"{nm.group(1)}{nm.group(2)}"
    return code


def course_parser(course):
    """Course parser

    Args:
        course (dict): Course

    Returns:
        (dict): Parsed course
    """
    if not course["courseCode"]:
        if course["courseName"].find("[ AE ]") != -1:
            course["courseType"] = "ae"
        elif course["courseName"].find("[ NAE ]") != -1:
            if (
                    course["courseName"].find("Foreign") != -1
                    or course["courseName"].find("Xarici") != -1
            ):
                course["courseType"] = "lang"
            else:
                course["courseType"] = "nae"
        course.pop("courseName")
        course.pop("courseCode")
    else:
        course["courseType"] = "def"

    return course


def courses_parser(course_group):
    """Courses parser

    Args:
        course_group (list): List of raw courses

    Returns:
        (list): Courses
    """
    courses = []
    # Iterating through subjects while ignoring header.
    for subject in course_group[1:]:
        row = {}
        # Iterating through fields of the subject with index.
        for i, j in enumerate(subject):
            # Skip if it is empty or a number column.
            if course_group[0][i] == "№" or (
                    not course_group[0][i].strip() and not j.strip()
            ):
                continue
            # Migrate / Translate fields.
            match header := migrate.get(course_group[0][i], course_group[0][i]):
                case "courseCode":
                    j = course_code_parser(j)
                case "ects" | "theory":
                    j = int(j)
            row[header] = migrate.get(j, j)
        courses.append(course_parser(row))
    return courses


def references_parser(references):
    """References Parser

    Args:
          references (list): List of raw reference

    Returns:
          (list): Parsed references
    """
    refs = []
    # Iterating through subjects while ignoring header.
    for subject in references[1:]:
        row = {}
        mc = 0
        # Iterating through fields of the subject with index.
        for i, j in enumerate(subject):
            # Skip if it is empty or a number column.
            if references[0][i] == "№" or (
                    not references[0][i].strip() and not j.strip()
            ):
                continue
            # Migrate / Translate fields.
            header = ref_migrate[mc]
            if header in {"oldCourseCode", "newCourseCode"}:
                j = course_code_parser(j)
            elif header == "year":
                j = int(j)
            mc += 1
            row[header] = migrate.get(j, j)
        refs.append(row)
    return refs


# Translation table
migrate = {
    "Course Code": "courseCode",
    "Name": "courseName",
    "Theory": "theory",
    "Dərs kodu": "courseCode",
    "Adı": "courseName",
    "Nəz": "theory",
    "Non-area lective subject": "nonAreaCourse",
    "Area elective Course": "areaCourse",
    "Area Elective subject": "areaCourse",
    "Foreign language": "langCourse",
    "XXX XXX": "",
    "Year": "year",
}

# Reference translation table
ref_migrate = [
    "oldCourseCode",
    "oldCourseName",
    "year",
    "newCourseCode",
    "newCourseName",
]
