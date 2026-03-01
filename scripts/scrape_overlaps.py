import requests
from bs4 import BeautifulSoup
import json
import concurrent.futures
import re
import urllib3
urllib3.disable_warnings()

def fetch_overlaps(course_id):
    url = f"https://www3.openu.ac.il/ouweb/owal/chofef.list?kurs_p={course_id}&machlaka_akademit_p=000&daf_p=0&sug_p=I"
    try:
        response = requests.get(url, timeout=15, verify=False)
        response.encoding = 'windows-1255'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tables = soup.find_all('table')
        if len(tables) < 3:
            return course_id, []
            
        target_table = tables[2] # Usually the third table contains the data
        
        combinations = []
        current_combo = None
        
        for tr in target_table.find_all('tr'):
            # Check if it's a separator
            if tr.find('hr'):
                if current_combo and len(current_combo['courses']) > 1:
                    combinations.append(current_combo)
                current_combo = None
                continue
                
            tds = tr.find_all('td')
            if len(tds) >= 7:
                # This is a course row
                combo_points_td = tds[0].get_text(strip=True).replace('\xa0', '')
                course_points_td = tds[1].get_text(strip=True).replace('\xa0', '')
                course_id_td = tds[6].get_text(strip=True)
                
                # Extract digits only for course id
                c_match = re.search(r'\d{5}', course_id_td)
                if not c_match:
                    continue
                c_id = c_match.group(0)
                
                # New combination block starts if combo_points_td is not empty
                if combo_points_td and combo_points_td.isdigit():
                    if current_combo and len(current_combo['courses']) > 1:
                        combinations.append(current_combo)
                    current_combo = {
                        "combination_credits": int(combo_points_td),
                        "courses": []
                    }
                    
                if current_combo is not None:
                    current_combo["courses"].append(c_id)
        
        # Add the last one if exists
        if current_combo and len(current_combo['courses']) > 1:
            combinations.append(current_combo)
            
        return course_id, combinations
    except Exception as e:
        print(f"Error for {course_id}: {e}")
        return course_id, []

def main():
    print("Loading enriched_courses.json to get all course IDs...")
    with open('enriched_courses.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    course_ids = list(data.keys())
    print(f"Found {len(course_ids)} courses. Fetching overlaps...")
    
    overlaps_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_course = {executor.submit(fetch_overlaps, cid): cid for cid in course_ids}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_course)):
            cid, combos = future.result()
            if combos:
                overlaps_data[cid] = combos
            if (i+1) % 50 == 0:
                print(f"Processed {i+1}/{len(course_ids)} courses...")
                
    # The output might have duplicates because combinations are bidirectional.
    # We can deduplicate by sorting course lists and converting to string
    unique_combinations = {}
    for cid, combos in overlaps_data.items():
        for combo in combos:
            courses = sorted(combo['courses'])
            key = f"{combo['combination_credits']}-" + "-".join(courses)
            unique_combinations[key] = {
                "courses": courses,
                "combination_credits": combo['combination_credits']
            }
            
    final_overlaps = list(unique_combinations.values())
    print(f"Found {len(final_overlaps)} unique overlapping course groups.")
    
    with open('course_overlaps.json', 'w', encoding='utf-8') as f:
        json.dump(final_overlaps, f, indent=2, ensure_ascii=False)
        
    print("Saved to course_overlaps.json")

if __name__ == '__main__':
    main()
