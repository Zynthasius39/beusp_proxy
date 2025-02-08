from bs4 import BeautifulSoup


def deps(text):
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


def deps2(text):
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
