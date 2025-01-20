def home_parser_offline():
    """Home Parser (Offline)"""
    return read_json_file("demo/home.json")

def grades_parser_offline():
    """Grade Options Parser (Offline)"""
    return read_json_file("demo/grades_options.json")

def grades_all_parser_offline():
    """All Grade Parser (Offline)"""
    return read_json_file("demo/grades_all.json")

def faq_parser_offline():
    """FAQ Parser (Offline)"""
    return read_json_file("demo/faq.json")

def announces_parser_offline():
    """Announce Parser (Offline)"""
    return read_json_file("demo/announces.json")

def deps_parser_offline():
    """Department Parser (Offline)"""
    return read_json_file("demo/deps.json")

def transcript_parser_offline():
    """Transcript Parser (Offline)"""
    return read_json_file("demo/transcript.json")

def grades2_parser_offline():
    """Grade Parser (Offline)"""
    return read_json_file("demo/grades.json")

def attendance2_parser_offline():
    """Attendance Parser by Course (Offline)"""
    return read_json_file("demo/attendance2.json")

def attendance3_parser_offline():
    """Attendance Parser by Student (Offline)"""
    return read_json_file("demo/attendance3.json")

def deps2_parser_offline():
    """Departments Parser by Code (Offline)"""
    return read_json_file("demo/deps2.json")

def program_parser_offline():
    """Program Parser (Offline)"""
    return read_json_file("demo/program.json")

def msg_parser_offline():
    """Message Parser (Offline)"""
    return read_json_file("demo/msg.json")

def read_json_file(path):
    """Read JSON file in the given path

    Args:
        path (str): File path

    Returns:
        str: File contents
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""
