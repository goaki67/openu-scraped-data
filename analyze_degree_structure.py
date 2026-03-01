import requests
from bs4 import BeautifulSoup
import urllib3
import re
urllib3.disable_warnings()

url = "https://academic.openu.ac.il/CS/computer/program/AF.aspx"
res = requests.get(url, verify=False)
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, 'html.parser')

print("Degree Blocks:")
# The main container
curriculum = soup.find('div', class_='curriculum')

if curriculum:
    # Iterate through direct children or find all logical blocks
    # Looking at the class names, they probably use headers followed by 'table-d-flex' divs
    for child in curriculum.descendants:
        if child.name in ['h2', 'h3', 'h4']:
            print(f"\n--- HEADER: {child.get_text(strip=True)} ---")
        elif child.name == 'div' and 'table-d-flex' in child.get('class', []):
            courses = child.find_all('a', href=True)
            for a in courses:
                if re.search(r'/courses/\d{5}\.htm', a['href'], re.I):
                    c_id = re.search(r'\d{5}', a['href']).group()
                    print(f"  - {c_id}: {a.get_text(strip=True)[:30]}...")
