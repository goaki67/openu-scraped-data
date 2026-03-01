import json
from bs4 import BeautifulSoup
import re

def extract_metadata():
    with open('scraped_course_pages.jsonl', 'r', encoding='windows-1255') as f:
        for i, line in enumerate(f):
            if i > 20: break
            try:
                data = json.loads(line)
            except:
                continue
            html = data.get('html', '')
            course_id = data.get('course_id')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Find lines containing credit info
            lines = text.split('\\n')
            for l in lines:
                if 'נקודות זכות' in l or 'נ"ז' in l or 'רמה' in l or 'ברמה' in l or 'סמינריונית' in l:
                    print(f"{course_id}: {l.strip()}")

if __name__ == '__main__':
    extract_metadata()
