import re

from bs4 import BeautifulSoup


def home(text):
    """Homepage parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # TODO: Convert to schema
    soup = BeautifulSoup(text, "html.parser")

    student_info_table = {}
    # Find main table with given class name.
    for tr in soup.find("table", class_="table").find_all("tr")[1:]:
        cells = tr.find_all("td")
        if cells:
            # Clean the cell, parse field and value.
            field = re.sub(
                r"\s\s+", " ", cells[0].text.replace(":", "").strip().replace("\n", "")
            )
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
        r"(?<==)(.*?)(?=&)", soup.find("img", class_="img-circle")["src"].strip()
    )[0]

    return {
        "home": {
            "student_info": student_info_table,
            "documents": documents_table,
            "image": image_url,
        }
    }
