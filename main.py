import argparse
import os
import sys
import subprocess

def run_script(script_path, args=None):
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="OpenU Scraper & DB CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Scrape command
    scrape_p = subparsers.add_parser("scrape", help="Scrape data")
    scrape_p.add_argument("--course", help="Scrape a single course ID")
    scrape_p.add_argument("--all-courses", action="store_true", help="Scrape all courses")
    scrape_p.add_argument("--degrees", action="store_true", help="Scrape all degrees")
    scrape_p.add_argument("--overlaps", action="store_true", help="Scrape all overlaps")

    # Update DB command
    update_p = subparsers.add_parser("update-db", help="Update the SQLite database")
    update_p.add_argument("--all", action="store_true", help="Update everything")

    args = parser.parse_args()

    if args.command == "scrape":
        if args.course:
            print(f"Scraping course: {args.course}...")
            run_script("scripts/scrape_single_course.py", [args.course])
        elif args.all_courses:
            print("Scraping all courses...")
            run_script("scripts/scrape_all_courses.py")
        elif args.degrees:
            print("Scraping all degrees...")
            run_script("scripts/scrape_degrees.py")
            run_script("scripts/advanced_degree_parser.py")
        elif args.overlaps:
            print("Scraping all overlaps...")
            run_script("scripts/scrape_overlaps_regex.py")

    elif args.command == "update-db":
        print("Updating SQLite database...")
        # 1. Build base course DB
        run_script("scripts/build_planner_db.py")
        # 2. Add degrees
        run_script("scripts/update_db_degrees.py")
        # 3. Add overlaps
        run_script("scripts/update_db_overlaps.py")
        print("\nDatabase update complete: openu_planner.db")

if __name__ == "__main__":
    main()
