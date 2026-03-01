import json
import sqlite3

def update_db_with_degrees():
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    # Create tables for degrees
    c.execute('''DROP TABLE IF EXISTS degrees''')
    c.execute('''DROP TABLE IF EXISTS degree_courses''')
    
    c.execute('''
        CREATE TABLE degrees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            requirements_text TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE degree_courses (
            degree_id INTEGER,
            course_id TEXT,
            FOREIGN KEY(degree_id) REFERENCES degrees(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    print("Loading open_u_degrees.json...")
    try:
        with open('open_u_degrees.json', 'r', encoding='utf-8') as f:
            degrees_data = json.load(f)
            
        for degree in degrees_data:
            title = degree.get('title', '')
            url = degree.get('url', '')
            req_text = json.dumps(degree.get('requirements_text', []), ensure_ascii=False)
            
            c.execute('INSERT INTO degrees (title, url, requirements_text) VALUES (?, ?, ?)', (title, url, req_text))
            degree_id = c.lastrowid
            
            for course_id in degree.get('courses', []):
                # Only insert if the course exists (optional, but good for referential integrity)
                # We'll just insert it directly
                c.execute('INSERT INTO degree_courses (degree_id, course_id) VALUES (?, ?)', (degree_id, course_id))
                
        conn.commit()
        print("Successfully added degrees and degree_courses to openu_planner.db!")
    except Exception as e:
        print("Error processing degrees:", e)
        
    conn.close()

if __name__ == '__main__':
    update_db_with_degrees()
