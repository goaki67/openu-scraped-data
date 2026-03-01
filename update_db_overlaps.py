import json
import sqlite3

def update_db_with_overlaps():
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    # Create tables for overlaps
    c.execute('''DROP TABLE IF EXISTS overlapping_groups''')
    c.execute('''DROP TABLE IF EXISTS overlapping_courses''')
    
    c.execute('''
        CREATE TABLE overlapping_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            max_credits INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE overlapping_courses (
            group_id INTEGER,
            course_id TEXT,
            FOREIGN KEY(group_id) REFERENCES overlapping_groups(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    print("Loading course_overlaps.json...")
    try:
        with open('course_overlaps.json', 'r', encoding='utf-8') as f:
            overlaps_data = json.load(f)
            
        for group in overlaps_data:
            max_credits = group.get('combination_credits', 0)
            courses = group.get('courses', [])
            
            c.execute('INSERT INTO overlapping_groups (max_credits) VALUES (?)', (max_credits,))
            group_id = c.lastrowid
            
            for course_id in courses:
                c.execute('INSERT INTO overlapping_courses (group_id, course_id) VALUES (?, ?)', (group_id, course_id))
                
        conn.commit()
        print("Successfully added overlapping_groups and overlapping_courses to openu_planner.db!")
    except Exception as e:
        print("Error processing overlaps:", e)
        
    conn.close()

if __name__ == '__main__':
    update_db_with_overlaps()
