import json
import bs4

def search_overlaps():
    count = 0
    with open('scraped_course_pages.jsonl', 'r', encoding='windows-1255') as f:
        for line in f:
            try:
                data = json.loads(line)
                html = data.get('html', '')
                if 'חפיפ' in html or 'חופפ' in html:
                    soup = bs4.BeautifulSoup(html, 'html.parser')
                    
                    # Sometimes overlaps are linked:
                    # <a href="https://www3.openu.ac.il/ouweb/owal/chofef.list?kurs_p=00000...">
                    for a in soup.find_all('a'):
                        if 'chofef.list' in a.get('href', ''):
                            print(f"{data['course_id']}: {a['href']}")
                            count += 1
                            if count >= 10:
                                return
            except Exception as e:
                pass

if __name__ == '__main__':
    search_overlaps()
