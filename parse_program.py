import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

def fetch_program_requirements(url):
    response = requests.get(url, verify=False)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print(f"TITLE: {soup.title.get_text() if soup.title else 'No Title'}")
    
    # OpenU program pages usually have tables of courses or specific sections.
    # Let's find all courses listed.
    courses = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(r'/courses/(\d{5})\.htm', href)
        if match:
            courses.add(match.group(1))
            
    print(f"FOUND {len(courses)} courses in the program.")
    
    # We can also look for specific text describing requirements, like "לפחות 108 נ"ז"
    for p in soup.find_all(['p', 'li', 'td']):
        text = p.get_text(strip=True)
        if 'נ"ז' in text or 'נקודות זכות' in text:
            print("REQ:", text[:100])

if __name__ == '__main__':
    fetch_program_requirements("https://academic.openu.ac.il/CS/computer/program/AF.aspx")
