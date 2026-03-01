import json
import requests
import concurrent.futures
import os
import time

def scrape_course(course_id):
    url = f"https://www.openu.ac.il/courses/{course_id}.htm"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'windows-1255'
        if res.status_code == 200:
            return {"course_id": course_id, "html": res.text}
    except Exception as e:
        print(f"Error {course_id}: {e}")
    return None

def main():
    print("Loading master course list...")
    try:
        with open("data/master_course_list.json", "r", encoding="utf-8") as f:
            courses = json.load(f)
    except:
        print("Master course list not found.")
        return

    ids = [c.get("course_id") for c in courses]
    print(f"Scraping {len(ids)} courses...")

    os.makedirs("data", exist_ok=True)
    with open("data/scraped_course_pages.jsonl", "w", encoding="windows-1255") as f:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_id = {executor.submit(scrape_course, cid): cid for cid in ids}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_id)):
                res = future.result()
                if res:
                    f.write(json.dumps(res) + "\n")
                if (i+1) % 50 == 0:
                    print(f"Scraped {i+1}/{len(ids)} courses...")

if __name__ == "__main__":
    main()
