import sqlite3
import json
import sys

def get_degree_plan(degree_id):
    conn = sqlite3.connect('openu_planner.db')
    c = conn.cursor()
    
    # 1. Fetch degree info
    c.execute("SELECT name, url, requirements_json FROM degrees WHERE id = ?", (degree_id,))
    res = c.fetchone()
    if not res:
        print(f"Degree '{degree_id}' not found.")
        return
    
    name, url, req_text_json = res
    print(f"\n# Degree: {name}")
    print(f"URL: {url}")
    
    # 2. Fetch blocks
    c.execute("SELECT id, header, type, required_credits FROM degree_blocks WHERE degree_id = ?", (degree_id,))
    blocks = c.fetchall()
    
    for b_id, header, b_type, credits in blocks:
        print(f"\n## Block: {header}")
        print(f"Type: {b_type} | Required Credits: {credits if credits else 'N/A'}")
        
        # 3. Fetch courses in this block
        c.execute("""
            SELECT c.id, c.name, c.credits, c.level 
            FROM degree_courses dc
            JOIN courses c ON dc.course_id = c.id
            WHERE dc.block_id = ?
        """, (b_id,))
        courses = c.fetchall()
        
        if courses:
            print(f"{'ID':<10} | {'Name':<40} | {'Cr':<3} | {'Level':<10}")
            print("-" * 75)
            for cid, cname, ccredits, clevel in courses:
                clean_name = cname.replace('\u202b', '').replace('\u202c', '').strip()
                print(f"{cid:<10} | {clean_name[:40]:<40} | {ccredits:<3} | {clevel:<10}")
        else:
            print("  (No specific courses listed in this block)")

    # 4. Other requirements (from raw text if available)
    if req_text_json:
        reqs = json.loads(req_text_json)
        if reqs:
            print("\n## Other General Requirements (from text):")
            for r in reqs:
                if len(r.strip()) > 20: # Only meaningful lines
                    print(f"- {r.strip()}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_degree_plan(sys.argv[1])
    else:
        # List some examples if no ID provided
        print("Usage: python3 get_degree_plan.py <degree_id>")
        print("\nAvailable degree examples (ID):")
        conn = sqlite3.connect('openu_planner.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM degrees LIMIT 10")
        for row in c.fetchall():
            print(f"  {row[0]:<40} | {row[1]}")
        conn.close()
