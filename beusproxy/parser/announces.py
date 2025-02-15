from bs4 import BeautifulSoup

from ..common.utils import parse_date


def announces(text):
    """Announces parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    anns_list = []
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
        # Append Announce to anns_list.
        anns_list.append(
            {
                "name": subdivs[0].i.text.strip().capitalize(),
                "body": subdivs[1].text.strip(),
                "date": parse_date(subdivs[2].text.strip()),
            }
        )

    return anns_list
