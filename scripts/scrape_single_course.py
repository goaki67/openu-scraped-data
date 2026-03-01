import json
import requests
import sys
import os

def scrape_single_course(course_id):
    url = f"https://www.openu.ac.il/courses/{course_id}.htm"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'windows-1255'
        if res.status_code == 200:
            course_data = {
                "course_id": course_id,
                "html": res.text
            }
            # Append to scraped_course_pages.jsonl
            os.makedirs("data", exist_ok=True)
            with open("data/scraped_course_pages.jsonl", "a", encoding="windows-1255") as f:
                f.write(json.dumps(course_data) + "\n")
            print(f"Successfully scraped course {course_id} and added to data/scraped_course_pages.jsonl")
        else:
            print(f"Course {course_id} not found (Status Code: {res.status_code})")
    except Exception as e:
        print(f"Error scraping course {course_id}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape_single_course(sys.argv[1])
    else:
        print("Usage: python3 scripts/scrape_single_course.py <course_id>")
