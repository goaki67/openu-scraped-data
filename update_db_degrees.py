import json
import sqlite3

def update_db_with_advanced_degrees():
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    # Create tables for degrees
    c.execute('''DROP TABLE IF EXISTS degree_courses''')
    c.execute('''DROP TABLE IF EXISTS degree_blocks''')
    c.execute('''DROP TABLE IF EXISTS degrees''')
    
    c.execute('''
        CREATE TABLE degrees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            requirements_text TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE degree_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            degree_id INTEGER,
            header TEXT,
            type TEXT,
            required_credits INTEGER,
            FOREIGN KEY(degree_id) REFERENCES degrees(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE degree_courses (
            degree_id INTEGER,
            block_id INTEGER,
            course_id TEXT,
            FOREIGN KEY(degree_id) REFERENCES degrees(id),
            FOREIGN KEY(block_id) REFERENCES degree_blocks(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    print("Loading basic degree metadata...")
    try:
        with open('open_u_degrees.json', 'r', encoding='utf-8') as f:
            basic_data = json.load(f)
            basic_dict = {d['url']: d for d in basic_data}
    except:
        basic_dict = {}

    print("Loading advanced_degrees.json...")
    try:
        with open('advanced_degrees.json', 'r', encoding='utf-8') as f:
            degrees_data = json.load(f)
            
        for degree in degrees_data:
            title = degree.get('title', '')
            url = degree.get('url', '')
            
            # Get old requirements text if exists
            old_reqs = basic_dict.get(url, {}).get('requirements_text', [])
            req_text = json.dumps(old_reqs, ensure_ascii=False)
            
            c.execute('INSERT INTO degrees (title, url, requirements_text) VALUES (?, ?, ?)', (title, url, req_text))
            degree_id = c.lastrowid
            
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
