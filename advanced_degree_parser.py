import json
import requests
from bs4 import BeautifulSoup
import re
import urllib3
import concurrent.futures

urllib3.disable_warnings()

def parse_advanced_degree(url, title):
    try:
        res = requests.get(url, verify=False, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        curriculum = soup.find('div', class_='curriculum')
        if not curriculum:
            return {"url": url, "title": title, "blocks": []}
            
        blocks = []
        current_header = "כללי (General)"
        current_courses = []
        
        # In this structure, elements are siblings. We need to iterate over direct children of curriculum or the main containers.
        # But actually, the previous script iterated over `curriculum.descendants`. This causes duplicate visits if `table-d-flex` contains other things.
        # It's safer to find all headers and table-d-flex divs in order.
        elements = curriculum.find_all(['h2', 'h3', 'h4', 'div'])
        
        for el in elements:
            if el.name in ['h2', 'h3', 'h4']:
                # Save previous block if it has courses
                if current_courses:
                    blocks.append({
                        "header": current_header,
                        "courses": list(set(current_courses))
                    })
                    current_courses = []
                    
                current_header = el.get_text(strip=True).replace('\u202b', '').replace('\u202c', '')
                
            elif el.name == 'div' and 'table-d-flex' in el.get('class', []) and not 'table-d-flex-body' in el.get('class', []):
                # We want the main container to avoid double counting inner divs
                for a in el.find_all('a', href=True):
                    match = re.search(r'/courses/(\d{5})\.htm', a['href'], re.I)
                    if match:
                        current_courses.append(match.group(1))
                        
        if current_courses:
            blocks.append({
                "header": current_header,
                "courses": list(set(current_courses))
            })
            
        # Post-process blocks to extract type and credits
        for b in blocks:
            header = b["header"]
            b["type"] = "חובה" if "חובה" in header else ("בחירה" if "בחירה" in header else "לא מוגדר")
            
            # Try to extract credits
            credit_match = re.search(r'(\d+)\s*נ"ז', header)
            if credit_match:
                b["credits"] = int(credit_match.group(1))
            else:
                b["credits"] = None
                
        return {
            "url": url,
            "title": title,
            "blocks": blocks
        }
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return {"url": url, "title": title, "blocks": []}

def build_advanced_degrees():
    print("Loading basic degrees data...")
    with open('open_u_degrees.json', 'r', encoding='utf-8') as f:
        basic_degrees = json.load(f)
        
    print(f"Reparsing {len(basic_degrees)} degrees for advanced structure...")
    
    advanced_degrees = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_deg = {executor.submit(parse_advanced_degree, deg['url'], deg['title']): deg for deg in basic_degrees}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_deg)):
            res = future.result()
            if res:
                advanced_degrees.append(res)
            if (i+1) % 50 == 0:
                print(f"Processed {i+1}/{len(basic_degrees)} degrees...")
                
    print("Saving advanced_degrees.json...")
    with open('advanced_degrees.json', 'w', encoding='utf-8') as f:
        json.dump(advanced_degrees, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    build_advanced_degrees()
