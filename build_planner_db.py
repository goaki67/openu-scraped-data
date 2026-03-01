import json
import re
import sqlite3
from bs4 import BeautifulSoup

def extract_course_metadata():
    print("Loading existing AST and semester data...")
    try:
        with open('ast_prerequisites.json', 'r', encoding='utf-8') as f:
            ast_data = json.load(f)
    except Exception as e:
        print("Could not load ast_prerequisites.json:", e)
        ast_data = {}

    print("Parsing raw HTML for metadata...")
    courses_metadata = {}
    
    with open('scraped_course_pages.jsonl', 'r', encoding='windows-1255') as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                continue
                
            course_id = data.get('course_id')
            html = data.get('html', '')
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Clean invisible chars
            text = text.replace('\u200e', '').replace('\u200f', '').replace('\u202a', '').replace('\u202b', '').replace('\u202c', '')
            
            # TITLE & LANGUAGE
            title_elem = soup.find('title')
            title = title_elem.get_text().replace('\u202b', '').replace('\u202c', '').strip() if title_elem else ''
            
            language = None
            known_languages = ['אנגלית', 'ערבית', 'רוסית', 'צרפתית', 'ספרדית', 'גרמנית', 'איטלקית']
            for lang in known_languages:
                if f"({lang})" in title or f"(‏{lang}‎)" in title or f"({lang} " in title:
                    language = lang
                    break
            
            # CREDITS & LEVEL
            credits = 0
            level = "לא מוגדר"
            has_seminar = False
            
            lines = text.split('\\n')
            for l in lines:
                l_clean = l.strip()
                if not l_clean: continue
                
                # Check for "אינו מקנה נקודות זכות"
                if "אינו מקנה נקודות זכות" in l_clean:
                    credits = 0
                    level = "ללא נז"
                    break
                
                # Check for "<number> נקודות זכות"
                credit_match = re.search(r'(\d+)\s*נקודות\s*זכות', l_clean)
                if credit_match:
                    credits = int(credit_match.group(1))
                    
                    if "רמת פתיחה" in l_clean or "ברמת פתיחה" in l_clean:
                        level = "פתיחה"
                    elif "רמה רגילה" in l_clean or "ברמה רגילה" in l_clean:
                        level = "רגילה"
                    elif "רמה מתקדמת" in l_clean or "ברמה מתקדמת" in l_clean:
                        level = "מתקדמת"
                    elif "תואר שני" in l_clean:
                        level = "תואר שני"
                        
                    if "סמינריונית" in l_clean and "ללא אפשרות" not in l_clean:
                        has_seminar = True
                        
                    break # Assuming first match is the main one
            
            # DEPARTMENTS (שיוך)
            departments = []
            for l in lines:
                l_clean = l.strip()
                if l_clean.startswith('שיוך:'):
                    departments.append(l_clean.replace('שיוך:', '').strip())
            
            # Merge with AST data
            ast_course = ast_data.get(course_id, {})
            reqs = ast_course.get('requirements', {})
            semesters = ast_course.get('semesters', [])
            
            courses_metadata[course_id] = {
                "course_id": course_id,
                "name": title,
                "language": language,
                "credits": credits,
                "level": level,
                "has_seminar": has_seminar,
                "departments": departments,
                "semesters": semesters,
                "requirements": reqs
            }

    print("Writing to enriched_courses.json...")
    with open('enriched_courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses_metadata, f, indent=2, ensure_ascii=False)
        
    print("Building openu_planner.db SQLite database...")
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    c.execute('''DROP TABLE IF EXISTS courses''')
    c.execute('''DROP TABLE IF EXISTS prerequisites''')
    c.execute('''DROP TABLE IF EXISTS course_departments''')
    c.execute('''DROP TABLE IF EXISTS course_semesters''')
    
    c.execute('''
        CREATE TABLE courses (
            id TEXT PRIMARY KEY,
            name TEXT,
            language TEXT,
            credits INTEGER,
            level TEXT,
            has_seminar BOOLEAN,
            requirements_json TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE prerequisites (
            course_id TEXT,
            req_course_id TEXT,
            type TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(req_course_id) REFERENCES courses(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE course_departments (
            course_id TEXT,
            department TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE course_semesters (
            course_id TEXT,
            semester TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    for cid, info in courses_metadata.items():
        c.execute('''
            INSERT INTO courses (id, name, language, credits, level, has_seminar, requirements_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            cid, 
            info['name'], 
            info['language'], 
            info['credits'], 
            info['level'], 
            info['has_seminar'], 
            json.dumps(info['requirements'], ensure_ascii=False)
        ))
        
        for dept in info['departments']:
            c.execute('INSERT INTO course_departments VALUES (?, ?)', (cid, dept))
            
        for sem in info['semesters']:
            c.execute('INSERT INTO course_semesters VALUES (?, ?)', (cid, sem))
            
        # Add basic edges for graph traversal (just raw requirements without logic)
        # To do this safely, we recursively extract IDs from the requirements AST
        def extract_ids_from_ast(ast_node):
            if not ast_node: return set()
            if ast_node.get("type") == "COURSE":
                return {ast_node.get("id")}
            
            ids = set()
            for op in ast_node.get("operands", []):
                ids.update(extract_ids_from_ast(op))
            return ids
            
        reqs = info['requirements']
        darush_ids = extract_ids_from_ast(reqs.get('darush'))
        darush_ids.update(extract_ids_from_ast(reqs.get('kabala')))
        mumlats_ids = extract_ids_from_ast(reqs.get('mumlats'))
        
        for req_id in darush_ids:
            c.execute('INSERT INTO prerequisites VALUES (?, ?, ?)', (cid, req_id, 'darush_kabala'))
            
        for req_id in mumlats_ids:
            c.execute('INSERT INTO prerequisites VALUES (?, ?, ?)', (cid, req_id, 'mumlats'))
            
    conn.commit()
    conn.close()
    print("Successfully created openu_planner.db!")

if __name__ == '__main__':
    extract_course_metadata()
