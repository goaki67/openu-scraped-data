from neo4j import GraphDatabase
import json

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def get_needed_to(course_id):
    """
    Returns the strict requirement tree for a given course.
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    query = """
    MATCH path = (c:Course {id: $course_id})-[:HAS_PREREQUISITE|HAS_OPERAND*]->(req)
    RETURN [n in nodes(path) | labels(n)[0] + ' ' + coalesce(n.id, n.type)] AS logical_path
    """
    with driver.session() as session:
        result = session.run(query, course_id=course_id)
        paths = []
        for record in result:
            paths.append(record["logical_path"])
    driver.close()
    return paths

def get_what_requires(course_id):
    """
    Returns all courses that require the specified course anywhere in their logical tree.
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    query = """
    MATCH (c:Course {id: $course_id})<-[:HAS_PREREQUISITE|HAS_OPERAND*]-(target:Course)
    RETURN DISTINCT target.id AS id, target.name AS name
    """
    with driver.session() as session:
        result = session.run(query, course_id=course_id)
        courses = []
        for record in result:
            courses.append({"id": record["id"], "name": record["name"]})
    driver.close()
    return courses

def get_all_courses():
    """
    Returns a list of all courses in the database.
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    query = """
    MATCH (c:Course)
    RETURN c.id AS id, c.name AS name
    ORDER BY c.id
    """
    with driver.session() as session:
        result = session.run(query)
        courses = []
        for record in result:
            courses.append({"id": record["id"], "name": record["name"]})
    driver.close()
    return courses

if __name__ == "__main__":
    print("Testing the graph database queries...\n")
    
    print("=== 0. Listing some available courses ===")
    all_courses = get_all_courses()
    print(f"Total courses found: {len(all_courses)}")
    print("First 5 courses:")
    for c in all_courses[:5]:
        print(f" - {c['id']}: {c['name']}")
        
    course_id_to_test = "20589"
    print(f"=== 1. What is the strict requirement tree for {course_id_to_test}? ===")
    needed = get_needed_to(course_id_to_test)
    for path in needed:
        print(" -> ".join(path))
        
    course_to_unlock = "20474"
    print(f"\n=== 2. What courses require {course_to_unlock} (Infinitesimal Calculus 1)? ===")
    unlocks = get_what_requires(course_to_unlock)
    for course in unlocks:
        print(f" - {course['id']}: {course['name']}")
