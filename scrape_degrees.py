import requests
from bs4 import BeautifulSoup
import re
import json
import urllib3
import concurrent.futures

urllib3.disable_warnings()

BASE_URL = "https://academic.openu.ac.il"

def get_soup(url):
    try:
        res = requests.get(url, verify=False, timeout=10)
        res.encoding = 'utf-8'
        return BeautifulSoup(res.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_programs_pages():
    soup = get_soup(f"{BASE_URL}/degrees/Pages/ba.aspx")
    if not soup: return []
    
    programs_urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'programs.aspx' in href.lower() or 'modelprograms.aspx' in href.lower():
            if href.startswith('http'):
                programs_urls.add(href)
            else:
                programs_urls.add(BASE_URL + href)
    return list(programs_urls)

def find_degree_links(programs_url):
    soup = get_soup(programs_url)
    if not soup: return []
    
    degree_links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if 'program/' in href.lower() and href.endswith('.aspx'):
            if href.startswith('http'):
                degree_links.add(href)
            elif href.startswith('/'):
                degree_links.add(BASE_URL + href)
            else:
                # relative link, hacky fix
                parts = programs_url.split('/')
                base = '/'.join(parts[:-2])
                degree_links.add(f"{base}/{href}")
    return list(degree_links)

def parse_degree(url):
    soup = get_soup(url)
    if not soup: return None
    
    title_elem = soup.find('h1')
    if not title_elem:
        title_elem = soup.title
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Degree"
    
    # Extract structural text (requirements)
    requirements_text = []
    for p in soup.find_all(['p', 'li']):
        text = p.get_text(strip=True)
        if 'נ"ז' in text or 'נקודות זכות' in text:
            requirements_text.append(text)
            
    # Extract courses mentioned in the program
    courses = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(r'/courses/(\d{5})\.htm', href)
        if match:
            courses.add(match.group(1))
            
    return {
        "url": url,
        "title": title.replace('\u202b', '').replace('\u202c', '').strip(),
        "total_courses_mentioned": len(courses),
        "courses": list(courses),
        "requirements_text": list(set(requirements_text))
    }

def main():
    print("Finding program index pages...")
    program_pages = find_programs_pages()
    print(f"Found {len(program_pages)} program indexes.")
    
    print("Finding individual degree links...")
    all_degree_links = set()
    for p_url in program_pages:
        links = find_degree_links(p_url)
        all_degree_links.update(links)
        
    print(f"Found {len(all_degree_links)} unique degrees. Scraping them now...")
    
    degrees_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(parse_degree, url): url for url in all_degree_links}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            res = future.result()
            if res:
                degrees_data.append(res)
            if (i+1) % 10 == 0:
                print(f"Scraped {i+1}/{len(all_degree_links)} degrees...")
                
    with open('open_u_degrees.json', 'w', encoding='utf-8') as f:
        json.dump(degrees_data, f, indent=2, ensure_ascii=False)
        
    print("Done! Saved to open_u_degrees.json")

if __name__ == '__main__':
    main()
