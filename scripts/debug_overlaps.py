import requests
from bs4 import BeautifulSoup
import re

url = "https://www3.openu.ac.il/ouweb/owal/chofef.list?kurs_p=20109&machlaka_akademit_p=000&daf_p=0&sug_p=I"
response = requests.get(url, verify=False)
response.encoding = 'windows-1255'
soup = BeautifulSoup(response.text, 'html.parser')

tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, t in enumerate(tables):
    rows = t.find_all('tr')
    print(f"Table {i}: {len(rows)} rows")
    if len(rows) > 5:
        for j, row in enumerate(rows[:5]):
            print(f"  Row {j}: {[td.get_text(strip=True) for td in row.find_all('td')]}")
