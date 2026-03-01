# OpenU Course Prerequisite Graph & Degree Planner

This project provides a robust, mathematically accurate data representation of course prerequisites and degree structures from the Open University of Israel (OpenU). It parses complex HTML phrasing, correctly injects alternative paths hidden within footnotes, builds a true Abstract Syntax Tree (AST) for course logic, and scrapes mutually exclusive courses (חפיפות). 

The data is available both as raw JSON and compiled into **SQLite** and **Neo4j** databases, allowing for powerful querying (like finding exact dependency trees, checking degree requirements, or seeing what courses a specific class unlocks).

This repository is designed to be the backend data source for a frontend framework like Next.js, specifically aimed at building a **Topological Course Recommender / Degree Planner**.

---

## 📂 Codebase Overview

Here is an explanation of every file in the repository and the pipeline that generates the data.

### 1. Raw Data & Parsed JSONs
* **`scraped_course_pages.jsonl`**: (Not tracked in git by default due to size). The raw scraped HTML of every single course page on the OpenU website.
* **`ast_prerequisites.json`**: The output of the AST parser. Contains every course, its title, available semesters, and the parsed boolean logic tree (`AND`, `OR`) representing its strict prerequisites.
* **`enriched_courses.json`**: Contains the courses merged with metadata like credits, academic level (פתיחה/רגילה/מתקדמת), language, and whether it requires a seminar paper.
* **`course_overlaps.json`**: Contains lists of mutually exclusive or overlapping courses (קורסים חופפים), detailing the maximum credits allowed for a given group.
* **`open_u_degrees.json`**: Contains over 500 OpenU degrees and tracks, listing the required/elective courses and the textual rules.

### 2. Python Parsing Scripts (The Pipeline)
* **`generate_ast.py`**: Parses the raw HTML from the `.jsonl` file. Resolves hidden footnotes and turns the Hebrew text prerequisites into a strict mathematical AST (saved to `ast_prerequisites.json`).
* **`fetch_semesters.py`**: Scrapes the OpenU API to find the exact semesters a course is offered (e.g., 2026א) and appends it to the JSON.
* **`scrape_overlaps_regex.py`**: Hits the OpenU overlapping courses database to find all course combinations that reduce total credits, outputting to `course_overlaps.json`.
* **`scrape_degrees.py`** (and helpers `fetch_dept_programs.py`, `parse_program.py`): Crawls the OpenU degree catalog, parses curriculum tables, and generates `open_u_degrees.json`.

### 3. Database Builders
* **`build_planner_db.py`**: Reads the JSON data and builds the base `openu_planner.db` SQLite database (courses, credits, metadata, and direct prerequisite edges).
* **`update_db_degrees.py`**: Appends the degree structures and course-to-degree mappings into the SQLite database.
* **`update_db_overlaps.py`**: Appends the overlapping course restrictions into the SQLite database.
* **`populate_neo4j.py`**: Translates the AST JSON logic into Graph Nodes and ingests the entire university curriculum into a Neo4j Graph Database.

### 4. Query Examples & Helpers
* **`query_neo4j.py`**: Example Python functions showing how to query the Neo4j database (e.g., finding the logic tree, or finding what courses depend on Course X).
* **`find_10779_neo4j.py`**: A specific debug script demonstrating how to traverse the Neo4j graph for a specific course ID.

### 5. Databases
* **`openu_planner.db`**: The final, self-contained SQLite database ready to be consumed by your application.

---

## 🧠 How to Build a Topological Search / Recommender

With this database, you have all the pieces needed to build an automated academic advisor. Here is how you use the data to run a topological search algorithm in your Next.js application:

### The Goal
A student provides:
1. The courses they have already completed.
2. The degree they are pursuing.
3. The upcoming semester they are registering for.

The algorithm must return a list of optimal courses they can and should take next.

### The Algorithm Steps

#### Step 1: Filter by Degree & Availability
Query the SQLite database to narrow down the universe of courses:
1. Fetch all courses required or allowed by the student's chosen degree (`SELECT course_id FROM degree_courses WHERE degree_id = X`).
2. Filter that list down to courses actually offered in the target semester (`JOIN course_semesters`).

#### Step 2: Remove Taken & Overlapping Courses (חפיפות)
1. Remove all courses the student has already passed.
2. **Crucial:** Query the `overlapping_groups` table. If the student took Course A, and Course A shares an overlap group with Course B, remove Course B from the pool of recommendations. (Otherwise, you will recommend a class that yields 0 credits).

#### Step 3: Evaluate the Prerequisite AST (The Topological Sort)
For the remaining candidate courses, you must verify if the student is legally allowed to take them.
1. Fetch the `requirements_json` for the candidate course.
2. Write a recursive evaluation function in JavaScript/TypeScript:
   - If the node is `AND`: Check if the student has passed *all* child nodes.
   - If the node is `OR`: Check if the student has passed *at least one* child node.
   - If the node is a `COURSE`: Check if the course ID is in the student's completed list.
3. If the evaluation returns `true`, the candidate course is **unlocked**.

#### Step 4: Rank the Recommendations
Now you have a list of unlocked, available, non-overlapping courses. To make the recommender "smart", you sort them:
1. **Unlocks the most future courses:** (Query Neo4j: `MATCH (target)-[*]->(candidate) RETURN count(target)`). Recommend courses that act as bottlenecks (like Calculus 1).
2. **Fills Credit Requirements:** If the student needs advanced credits (`מתקדמת`), boost courses where `level = 'מתקדמת'`.

---

## 🛠 Setup & Usage

### Option 1: SQLite (Easiest for Next.js / React)
The SQLite database (`openu_planner.db`) is completely portable. Drop it into your Next.js `data/` folder and query it directly using `better-sqlite3`.

### Option 2: Neo4j Graph Database (Best for Advanced Logic Traversals)
1. Start Neo4j locally via Docker:
   ```bash
   docker run --name openu-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -d neo4j
   ```
2. Run the ingestion script:
   ```bash
   python populate_neo4j.py
   ```
