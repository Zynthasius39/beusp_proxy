from bs4 import BeautifulSoup


def deps(text):
    """Department parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # New headers
    headers = {
        "Code of the department": "depCode",
        "Department name": "depName",
        "Department specific course code prefixes": "depPrefixes",
        "Bölmə kodu": "depCode",
        "Bölmənin adı": "depName",
        "Bölməyə məxsus dərs kodu prefiksləri": "depPrefixes",
    }

    soup = BeautifulSoup(text, "html.parser")

    is_header_row = True
    # Collect table cells in a list for further processing.
    table = []
    # Find departments table with given class name.
    for tr in soup.find("div", class_="table-responsive").find_all("tr"):
        row = []
        for td in tr.find_all("td")[:-1]:
            # Append striped cells.
            if is_header_row and len(row) != 0:
                # Translate header.
                row.append(headers[td.text.strip()])
            else:
                row.append(td.text.strip())
        # Finally append the row to the list.
        is_header_row = False
        table.append(row)

    deps_list = []
    # Iterating through rows while ignoring header and last empty row.
    for i in table[1:-1]:
        row = {}
        # Iterating through cells with index.
        for inx, j in enumerate(i):
            if table[0][inx] == "№":
                continue
            if table[0][inx] == "depPrefixes":
                j = j.split(", ")
            row[table[0][inx]] = j
        deps_list.append(row)

    return deps_list


def deps2(text):
    """Department parser by department code

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    headers = {
        "Code": "progCode",
        "Language": "lang",
        "Program name (Specialty name)": "progName",
        "Year": "year",
        "Faculty": "faculty",
        "Kodu": "progCode",
        "Dil": "lang",
        "Proqramın adı (İxtisasın adı)": "progName",
        "İli": "year",
        "Aid olduğu fakültə": "faculty"
    }

    soup = BeautifulSoup(text, "html.parser")

    # Collect table cells in a list for further processing.
    table = []
    # Find department table with given class name.
    for tr in soup.find("table", class_="table box").find_all("tr"):
        row = []
        for td in tr.find_all("td"):
            row.append(td.text.strip())
        table.append(row)

    deps_list = []
    # Iterating through rows in table while ignoring header row.
    for i in table[1:]:
        row = {}
        # Iterating through cells with index.
        for inx, j in enumerate(i[1:]):
            # Match and translate header.
            header = headers[table[0][inx + 1]]
            match header:
                case "progCode" | "year":
                    j = int(j)
                case "lang":
                    j = j.lower()
            row[header] = j
        deps_list.append(row)

    return deps_list
