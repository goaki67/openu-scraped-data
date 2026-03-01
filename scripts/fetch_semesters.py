import json
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time

def fetch_course_semesters(course_id):
    url = f"https://www3.openu.ac.il/ouweb/owal/catalog.sel_list_semesters?kurs_in={course_id}"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'windows-1255'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        semesters = []
        ul = soup.find('ul', class_='list_square')
        if ul:
            for li in ul.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    semesters.append(text)
        return course_id, semesters
    except Exception as e:
        print(f"Error fetching {course_id}: {e}")
        return course_id, []

def main():
    print("Loading ast_prerequisites.json...")
    with open('ast_prerequisites.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    course_ids = list(data.keys())
    print(f"Found {len(course_ids)} courses. Fetching semesters...")
    
    # Use ThreadPoolExecutor to speed up fetching
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_course = {executor.submit(fetch_course_semesters, cid): cid for cid in course_ids}
        for future in concurrent.futures.as_completed(future_to_course):
            cid, semesters = future.result()
            results[cid] = semesters
            
    print("Updating metadata...")
    for cid, info in data.items():
        info['semesters'] = results.get(cid, [])
        
    with open('ast_prerequisites.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Done! Updated ast_prerequisites.json with semesters metadata.")

if __name__ == '__main__':
    main()
