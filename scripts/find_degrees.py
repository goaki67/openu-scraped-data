import requests
from bs4 import BeautifulSoup

def find_degrees():
    url = "https://www.openu.ac.il/degrees/"
    response = requests.get(url, verify=False)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/degrees/' in href or 'academic.openu.ac.il/programs' in href:
            links.add(href)
            
    for l in sorted(links):
        print(l)

if __name__ == '__main__':
    find_degrees()
