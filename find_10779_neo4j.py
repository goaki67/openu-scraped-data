from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def find_course(course_id):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    # Query 1: Get the course details
    print(f"--- Course Details for {course_id} ---")
    query_details = """
    MATCH (c:Course {id: $course_id})
    RETURN c.id AS id, c.name AS name, c.semesters AS semesters
    """
    with driver.session() as session:
        result = session.run(query_details, course_id=course_id)
        for record in result:
            print(f"ID: {record['id']}")
            print(f"Name: {record['name']}")
            print(f"Semesters: {record['semesters']}")
            
    # Query 2: What are its prerequisites?
    print(f"\\n--- Prerequisites for {course_id} ---")
    query_prereqs = """
    MATCH path = (c:Course {id: $course_id})-[:HAS_PREREQUISITE|HAS_OPERAND*]->(req)
    RETURN [n in nodes(path) | labels(n)[0] + ' ' + coalesce(n.id, n.type)] AS logical_path
    """
    with driver.session() as session:
        result = session.run(query_prereqs, course_id=course_id)
        paths = list(result)
        if not paths:
            print("No prerequisites found.")
        for record in paths:
            print(" -> ".join(record["logical_path"]))

    # Query 3: What courses require this?
    print(f"\\n--- Courses that require {course_id} ---")
    query_required_by = """
    MATCH (target:Course)-[:HAS_PREREQUISITE|HAS_OPERAND*]->(c:Course {id: $course_id})
    RETURN DISTINCT target.id AS id, target.name AS name
    """
    with driver.session() as session:
        result = session.run(query_required_by, course_id=course_id)
        required_by = list(result)
        if not required_by:
            print("Not a prerequisite for any other courses.")
        for record in required_by:
            print(f" - {record['id']}: {record['name']}")

    driver.close()

if __name__ == "__main__":
    find_course("10779")
