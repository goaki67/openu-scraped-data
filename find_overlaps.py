import json
import re

def search_overlaps():
    with open('scraped_course_pages.jsonl', 'r', encoding='windows-1255') as f:
        for line in f:
            try:
                data = json.loads(line)
                html = data.get('html', '')
                if 'חופפ' in html or 'שקול' in html or 'חפיפ' in html:
                    print(f"Found match in {data['course_id']}")
                    import bs4
                    soup = bs4.BeautifulSoup(html, 'html.parser')
                    for p in soup.find_all(['p', 'div']):
                        text = p.get_text()
                        if 'חופפ' in text or 'חפיפ' in text or 'שקול' in text:
                            print(f"  {text.strip()}")
                    break
            except Exception as e:
                continue

if __name__ == '__main__':
    search_overlaps()
