# OpenU Course Prerequisite Graph & Degree Planner

This project provides a robust, mathematically accurate data representation of course prerequisites and degree structures from the Open University of Israel. It parses complex HTML phrasing, correctly injects alternative paths hidden within footnotes, and builds a true Abstract Syntax Tree (AST) for course logic. 

The data is available both as raw JSON and compiled into **SQLite** and **Neo4j** databases, allowing for powerful querying (like finding exact dependency trees, checking degree requirements, or seeing what courses a specific class unlocks).

This repository is designed to be the backend data source for a frontend framework like Next.js.

---

## 📦 What's Included in the Data?

1. **Course Prerequisites AST (`ast_prerequisites.json`)**: Contains every course, its title, available semesters (e.g., `2026א`), and the mathematically parsed boolean logic for its prerequisites (`AND`, `OR`, `AT_LEAST_X`).
2. **Degree Programs (`open_u_degrees.json`)**: Contains over 500 OpenU degrees, diplomas, and tracks, including the full list of courses mentioned in the curriculum and the textual requirements.
3. **SQLite Planner Database (`openu_planner.db`)**: A ready-to-use relational database containing:
   - **`courses`**: Course metadata (credits, language, level, seminar flags).
   - **`prerequisites`**: Direct graph edges connecting courses to their requirements.
   - **`course_semesters`**: The semesters each course is offered.
   - **`degrees` & `degree_courses`**: Mapping of every degree to its required/elective courses.
   - **`overlapping_groups` & `overlapping_courses`**: Defines mutually exclusive or overlapping courses (חפיפות), and the maximum credits allowed for taking the combination.
4. **Neo4j Ingestion (`populate_neo4j.py`)**: A script to load the AST logic directly into a Neo4j Graph Database for deep tree traversals.

---

## 🛠 Setup & Usage

### Option 1: SQLite (Easiest for Next.js / React)

The SQLite database (`openu_planner.db`) is completely portable and requires no server setup. You can drop it into your Next.js `data/` folder and query it directly using `better-sqlite3`.

**Example Queries:**
*Find courses taught in English:*
```sql
SELECT id, name, credits FROM courses WHERE language = 'אנגלית';
```

*Find all degrees that include course 10779:*
```sql
SELECT d.title, d.url FROM degrees d 
JOIN degree_courses dc ON d.id = dc.degree_id 
WHERE dc.course_id = '10779';
```

*Check if a course has an overlap constraint:*
```sql
SELECT g.max_credits, c.id, c.name 
FROM overlapping_groups g
JOIN overlapping_courses oc ON g.id = oc.group_id
JOIN courses c ON oc.course_id = c.id
WHERE g.id IN (SELECT group_id FROM overlapping_courses WHERE course_id = '20109');
```

### Option 2: Neo4j Graph Database (Best for Advanced Logic Traversals)

If you want to evaluate deep prerequisite paths, use Neo4j.

1. Start Neo4j locally via Docker:
   ```bash
   docker run --name openu-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -d neo4j
   ```
2. Run the ingestion script:
   ```bash
   pip install neo4j
   python populate_neo4j.py
   ```
3. Query the graph! (e.g., *What does taking Calculus 1 unlock?*)
   ```cypher
   MATCH (target:Course)-[:HAS_PREREQUISITE|HAS_OPERAND*]->(c:Course {id: "20474"})
   RETURN DISTINCT target.id, target.name
   ```

---

## 🧠 Building a Topological Recommendation System

To build a complete topological course recommender (a system that tells you what you should take next based on what you've completed, your degree, and the upcoming semester), the current data provides almost everything you need.

The system now natively supports:
- **Strict Dependencies:** Via the parsed Boolean AST of prerequisites.
- **Mutual Exclusions (חפיפות):** Utilizing the `overlapping_groups` table to prevent recommending courses that yield 0 credits due to overlaps.
- **Availability:** Filtering recommendations based on the `course_semesters` table.

### The Final Step: Degree Structure AST (חובה vs. בחירה)
Currently, `open_u_degrees.json` lists *all* courses mentioned in a degree and provides the *textual rules* (e.g., "Take 24 credits from this list, and 3 mandatory courses"). To programmatically recommend the optimal path, you will need to parse those degree rules into an AST, separating courses into categories:
- Mandatory Core (לימודי חובה)
- Mandatory Elective Lists (בחירה מתוך רשימה)
- General Electives (בחירה חופשית)

Once you parse the degree structural rules into distinct buckets, your Next.js app can run a topological sort algorithm using the Neo4j/SQLite graph to say: *"Since you passed X, and you need 12 more credits in category Y for your degree, and Course Z is offered next semester without overlapping your previous courses—take Course Z!"*
