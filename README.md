# OpenU Course Prerequisite Graph & Degree Planner

This project provides a robust, mathematically accurate data representation of course prerequisites and degree structures from the Open University of Israel (OpenU).

## 📂 Project Structure

- `data/`: Raw and parsed JSON/JSONL files (Scraped HTML, AST, Overlaps, Degrees).
- `scripts/`: Python scripts for scraping, parsing, and database generation.
- `main.py`: The unified CLI for scraping and updating the database.
- `openu_planner.db`: Self-contained SQLite database for querying.
- `get_degree_plan.py`: Helper script to visualize a degree's required and elective courses.

## 🚀 Getting Started

### 1. Installation
```bash
# It is recommended to use a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Scraping Data
You can scrape specific courses or entire categories:
```bash
# Scrape a single course (adds it to data/scraped_course_pages.jsonl)
python3 main.py scrape --course 20441

# Scrape all degrees
python3 main.py scrape --degrees

# Scrape all course overlaps
python3 main.py scrape --overlaps
```

### 3. Updating the Database
After scraping or modifying JSON data, rebuild the SQLite database:
```bash
python3 main.py update-db
```

### 4. Exploring Degree Plans
Get a clean list of required and elective courses for a specific degree:
```bash
# List all available degree IDs
python3 get_degree_plan.py

# Get the plan for a specific degree (e.g., Computer Science)
python3 get_degree_plan.py CS/computer/program/EL
```

## 🧠 Database Schema (SQLite)

- `courses`: Metadata (credits, level, language, seminar).
- `prerequisites`: Direct edges for the prerequisite graph.
- `degrees`: Degree titles and general requirements.
- `degree_blocks`: Groups of courses (e.g., "Infrastructural", "Required").
- `degree_courses`: Mapping of course IDs to degrees and blocks.
- `overlapping_groups`: Mutually exclusive course restrictions.

## 🛠️ Recommender Algorithm (Topological Sort)
To build a recommender, query the database to:
1. Filter the universe of courses by the student's chosen degree (`degree_id`).
2. Filter by current semester availability.
3. Perform a topological sort on the remaining courses based on the `prerequisites` table to determine the optimal study path.
