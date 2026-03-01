import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

def fetch_department_programs(url):
    response = requests.get(url, verify=False)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        # We are looking for things that look like specific programs
        if 'program' in href.lower() or 'תוכנית' in text or 'תואר' in text:
            links.append((text, href))
            
    for text, href in links:
        print(f"{text}: {href}")

if __name__ == '__main__':
    fetch_department_programs("https://academic.openu.ac.il/cs/computer/pages/programs.aspx")
