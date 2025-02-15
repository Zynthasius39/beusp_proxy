from bs4 import BeautifulSoup


def faq(text):
    """FAQ parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    soup = BeautifulSoup(text, "html.parser")

    faq_list = []
    # Find FAQ sitting in ul element with given class name.
    for li in soup.find("ul", class_="timeline").find_all("li"):
        # Append FAQ item and body into a list.
        faq_list.append(
            {
                "question": li.find(class_="timeline-item").text.strip(),
                "answer": li.find(class_="timeline-body").text.strip(),
            }
        )

    return faq_list
