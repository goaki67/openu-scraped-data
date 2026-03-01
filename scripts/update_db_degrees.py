import json
import sqlite3
import urllib.parse

def update_db_with_advanced_degrees():
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    # Create tables for degrees
    c.execute('''DROP TABLE IF EXISTS degree_courses''')
    c.execute('''DROP TABLE IF EXISTS degree_blocks''')
    c.execute('''DROP TABLE IF EXISTS degrees''')
    
    c.execute('''
        CREATE TABLE degrees (
            id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT,
            requirements_json TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE degree_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            degree_id TEXT,
            header TEXT,
            type TEXT,
            required_credits INTEGER,
            FOREIGN KEY(degree_id) REFERENCES degrees(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE degree_courses (
            degree_id TEXT,
            block_id INTEGER,
            course_id TEXT,
            FOREIGN KEY(degree_id) REFERENCES degrees(id),
            FOREIGN KEY(block_id) REFERENCES degree_blocks(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    print("Loading basic degree metadata...")
    try:
        with open('data/open_u_degrees.json', 'r', encoding='utf-8') as f:
            basic_data = json.load(f)
            basic_dict = {d['url']: d for d in basic_data}
    except:
        basic_dict = {}

    print("Loading data/advanced_degrees.json...")
    try:
        with open('data/advanced_degrees.json', 'r', encoding='utf-8') as f:
            degrees_data = json.load(f)
            
        for degree in degrees_data:
            name = degree.get('title', '')
            url = degree.get('url', '')
            
            try:
                degree_id = urllib.parse.urlparse(url).path.strip('/').replace('.aspx', '')
            except:
                degree_id = url
            
            # Get old requirements text if exists
            old_reqs = basic_dict.get(url, {}).get('requirements_text', [])
            req_json = json.dumps(old_reqs, ensure_ascii=False)
            
            try:
                c.execute('INSERT INTO degrees (id, name, url, requirements_json) VALUES (?, ?, ?, ?)', (degree_id, name, url, req_json))
            except sqlite3.IntegrityError:
                continue
            
            for block in degree.get('blocks', []):
                header = block.get('header', '')
                b_type = block.get('type', 'לא מוגדר')
                credits = block.get('credits')
                
                c.execute('''
                    INSERT INTO degree_blocks (degree_id, header, type, required_credits) 
                    VALUES (?, ?, ?, ?)
                ''', (degree_id, header, b_type, credits))
                
                block_id = c.lastrowid
                
                for course_id in block.get('courses', []):
                    c.execute('''
                        INSERT INTO degree_courses (degree_id, block_id, course_id) 
                        VALUES (?, ?, ?)
                    ''', (degree_id, block_id, course_id))
                    
        conn.commit()
        print("Successfully added advanced degrees, blocks, and degree_courses to openu_planner.db!")
    except Exception as e:
        print("Error processing degrees:", e)
        
    conn.close()

if __name__ == '__main__':
    update_db_with_advanced_degrees()
