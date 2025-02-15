import json
import re

from bs4 import BeautifulSoup

from ..common.utils import parse_date


def msg(html):
    """Message IDs parser

    Args:
        html (str): HTML input

    Returns:
        list: List of message ids
    """
    msg_ids = []
    # Iterating through matches of regex and append it to list.
    # Regex is used to match message ids from html.
    for i in re.findall(r"(?<=onclick=\"ShowReceivedMessage\().*?(?=\))", html):
        msg_ids.append(i)
    return msg_ids


def msg2(text):
    """Message parser

    Args:
        text (str): HTML input

    Returns:
        dict: JSON output
    """
    # Seperate HTML from JSON
    # It is designed to keep DATA and CODE together.
    # Why would you even do that?
    soup = BeautifulSoup(json.loads(text)["DATA"], "html.parser")

    msg_table = {}
    header = soup.find_all("tr")
    body = soup.find("div", class_="mailbox-read-message")

    # If all fields exist, append them to msg_table.
    if header[0] and header[1] and header[2] and body:
        msg_table["from"] = re.sub(
            r"\s\s+", " ", header[0].find_all("td")[1].text.strip().replace("\n", "")
        )
        # Parse insane date formats to iso format
        # e.g. 15:03 PM ? Really ?
        msg_table["date"] = parse_date(re.sub(
            r"\s\s+", " ", header[1].find_all("td")[1].text.strip().replace("\n", "")
        ))
        msg_table["subject"] = re.sub(
            r"\s\s+", " ", header[2].find_all("td")[1].text.strip().replace("\n", "")
        )
        msg_table["body"] = re.sub(r"\s\s+", " ", body.text.strip())

    return msg_table


def msg_id(html):
    """Message ID parser

    Args:
        html (str): HTML input

    Returns:
        list: List of message ids
    """
    soup = BeautifulSoup(html, "html.parser")

    msg_ids = []
    # Iterating through matches of regex and append it to list.
    # Regex is used to match message ids from html.
    for i in soup.find_all("span", attrs={"style": "color:#1E1E1E ;font-weight:bold"}):
        for k in re.findall(r"(?<=\().*?(?=\))", i.parent.parent.attrs["onclick"]):
            msg_ids.append(k)
    return msg_ids
