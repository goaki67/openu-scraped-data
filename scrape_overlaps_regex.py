import requests
import json
import re
import urllib3
import concurrent.futures

urllib3.disable_warnings()

def fetch_overlaps(course_id):
    url = f"https://www3.openu.ac.il/ouweb/owal/chofef.list?kurs_p={course_id}&machlaka_akademit_p=000&daf_p=0&sug_p=I"
    try:
        response = requests.get(url, timeout=15, verify=False)
        html = response.text
        
        # Split by <hr> to get the groups
        parts = re.split(r'(?i)<hr>', html)
        
        combinations = []
        for part in parts:
            if 'mkurs=' not in part:
                continue
                
            # Extract all course IDs in this block
            # Course IDs are 5 digits at the end of td, or in mkurs=
            course_ids = re.findall(r'mkurs=(\d{5})', part)
            course_ids = list(set(course_ids)) # Deduplicate
            
            # Extract combination credits (usually the first number in the block)
            # <TD WIDTH=10% ALIGN=center><font size=-1>8</font></TD>
            pts_match = re.search(r'<TD WIDTH=10% ALIGN=center><font size=-1>(\d+)</font></TD>', part, re.IGNORECASE)
            combo_points = int(pts_match.group(1)) if pts_match else None
            
            if len(course_ids) > 1 and combo_points is not None:
                combinations.append({
                    "combination_credits": combo_points,
                    "courses": course_ids
                })
                
        return course_id, combinations
    except Exception as e:
        return course_id, []

def main():
    print("Loading enriched_courses.json to get all course IDs...")
    with open('enriched_courses.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    course_ids = list(data.keys())
    print(f"Found {len(course_ids)} courses. Fetching overlaps...")
    
    overlaps_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_course = {executor.submit(fetch_overlaps, cid): cid for cid in course_ids}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_course)):
            cid, combos = future.result()
            if combos:
                overlaps_data[cid] = combos
            if (i+1) % 100 == 0:
                print(f"Processed {i+1}/{len(course_ids)} courses...")
                
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
