import re

from bs4 import BeautifulSoup

from beusproxy.common.utils import parse_date


def home(text):
    """Homepage parser

    Args:
        text (str): HTML input from root server

    Returns:
        dict: parsed JSON output
    """
    # Translation table
    headers = {
        "Student number": "studentId",
        "Tələbə nömrəniz": "studentId",
        "Name surname patronymic": "fullNamePatronymic",
        "Ad soyad, ata adı": "fullNamePatronymic",
        "Birth date": "birthDate",
        "Doğum tarixi": "birthDate",
        "Program / Class": "_programClass",
        "İxtisas / Kurs": "_programClass",
        "Qrup kodu": "groupCode",
        "Advisor": "advisor",
        "Akademik məsləhətçi": "advisor",
        "Status": "status",
        "BEU e-mail": "beuEmail",
        "BMU Mail": "beuEmail",
        "State-funded": "stateFunded",
        "Dövlət sifarişli": "stateFunded",
        "Presidential scholarship": "presidentScholar",
        "Prezident təqaüdlü": "presidentScholar",
        "Last login date": "_lastLoginDate",
        "Sistemə son giriş tarixi": "_lastLoginDate",
        "Last login ip": "_lastLoginIp",
        "Sistemə son giriş ip": "_lastLoginIp",
        "Registration date": "registerDate",
        "Qeydiyyat tarixi": "registerDate",
        "Debt (dormitory)": "_dormDebt",
        "Yataqxana borcunuz": "_dormDebt",
        "Dissertation topic": "dissTopic",
        "Dissertasiya mövzusu": "dissTopic",
        "SEC exam score": "dimScore",
        "Qəbul balı": "dimScore",
        "Təhsil haqqı ödəniş forması": "_eduDebtType",
        "İllik Təhsil haqqı": "_eduDebtFirst",
    }
    soup = BeautifulSoup(text, "html.parser")

    student_info_table = {
        "eduDebt": {},
        "lastLogin": {},
        "speciality": {},
    }

    unk_counter = 0
    # Find main table with given class name.
    for tr in soup.find("table", class_="table").find_all("tr"):
        if cells := tr.find_all("td"):
            # Skip unnecessary rows.
            if len(cells) < 2:
                continue
            # Clean the cell, parse field and value.
            og_field = re.sub(
                r"\s\s+", " ", cells[-2].text.replace(":", "").strip().replace("\n", "")
            )
            if og_field.startswith("Education debt") or og_field.startswith("Təhsil haqqı borcunuz"):
                field = "_eduDebt"
            else:
                field = headers.get(og_field, f"_unkField{unk_counter}")
            unk_counter += 1
            value = cells[-1].text.strip()
            try:
                match field:
                    # Clean the advisor.
                    case "advisor":
                        value_val = value.split(" ")
                        student_info_table[field] = f"{value_val[0].lower().capitalize()} {value_val[1].lower().capitalize()}"
                    # Construct eduDebt.
                    case "_eduDebt":
                            m = re.search(r"\[(\d{4}) - (\d)]", og_field)
                            student_info_table["eduDebt"]["year"] = int(m.group(1))
                            student_info_table["eduDebt"]["semester"] = int(m.group(2))
                            m = re.search(r"(\d+) AZN", value)
                            student_info_table["eduDebt"]["amount"] = int(m.group(1))
                    case "_eduDebtType":
                        student_info_table["eduDebt"]["paymentType"] = edu_debt_payment_t.get(value, f"_unknown_edup_t.{value}")
                    case "_eduDebtFirst":
                        m = re.search(r"(\d+) AZN", value)
                        student_info_table["eduDebt"]["paymentAnnual"] = int(m.group(1))
                    # Construct dormDebt.
                    case "_dormDebt":
                        m = re.search(r"(\d+) AZN", value)
                        student_info_table["dormDebt"] = int(m.group(1))
                    # Construct lastLogin.
                    case "_lastLoginDate":
                        student_info_table["lastLogin"]["datetime"] = parse_date(value)
                    case "_lastLoginIp":
                        if m := re.search(r"^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", value):
                            student_info_table["lastLogin"]["ip"] = value
                    # Construct speciality.
                    case "_programClass":
                        if m := re.search(r"(.*)-(EN|AZ) / (\d)", value):
                            student_info_table["speciality"]["program"] = m.group(1)
                            student_info_table["speciality"]["lang"] = m.group(2).lower()
                            student_info_table["speciality"]["year"] = int(m.group(3))
                    # Parse dates.
                    case "birthDate" | "registerDate":
                        student_info_table[field] = parse_date(value)
                    # Cast to int.
                    case "studentId":
                        student_info_table[field] = int(value)
                    # Value mapping.
                    case "presidentScholar" | "stateFunded":
                        student_info_table[field] = value in tf_states
                    case "status":
                        student_info_table[field] = status_t.get(value, f"_unknown_status_t.{value}")
                    # Skip empty cells.
                    case "":
                        continue
                    # Add the field, skip raw values
                    case _:
                        # if not field.startswith("_"):
                        student_info_table[field] = value
            except (ValueError, AttributeError):
                pass

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
        "documents": documents_table,
        "image": image_url,
        "studentInfo": student_info_table,
    }

edu_debt_payment_t= {
    "DS": "state_funded"
}

status_t = {
    "Oxuyur": "studying"
}

tf_states = {
    "Yes", "Bəli"
}
