from bs4 import BeautifulSoup


def announces(text):
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
