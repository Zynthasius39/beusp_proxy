import json

import jsondiff


def grade_diff(grades, grades_old):
    """Grades table comparer"""
    diff_symbols = {jsondiff.delete, jsondiff.insert, jsondiff.update}

    diff = jsondiff.diff(grades_old, grades, syntax="rightonly")
    for ck, cv in diff.items():
        if ck not in diff_symbols:
            for symbol in diff_symbols:
                if cv.get(symbol):
                    print(f"{cv}: {cv[symbol]}")
                    del cv[symbol]
        print(ck)
        print(json.dumps(cv, indent=1))
