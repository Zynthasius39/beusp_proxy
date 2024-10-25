import requests
import json
from bs4 import BeautifulSoup

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Cookie": "PHPSESSID=fq4loc81tq022emu030vsfo2iu"
}
res = requests.post('https://my.beu.edu.az',
    data="ajx=1&mod=grades&action=GetGrades&yt=2024#1&1729271150675",
    headers=headers)

# with open('table.html', 'r') as file:
#     data = file.read().rstrip()

print(res.status_code)
print(res.text)

# soup = BeautifulSoup(res.json()["DATA"], 'html.parser')
# table = soup.find('table')

# headers = []
# for th in table.find_all('th'):
#     headers.append(th.text.strip())

# # Step 5: Extract table rows
# rows = []
# for tr in table.find_all('tr')[1:]:  # Skipping the header row (the first row)
#     cells = tr.find_all('td')
#     row = [cell.text.strip() for cell in cells]
#     rows.append(row)

# # Step 6: Convert to a list of dictionaries (if headers exist)
# table_data = []
# if headers:
#     for row in rows:
#         table_data.append(dict(zip(headers, row)))
# else:
#     table_data = rows

# # Step 7: Convert the table data to JSON
# json_data = json.dumps(table_data, indent=4, ensure_ascii=False)

# # Step 8: Print or save the JSON output
# print(json_data)