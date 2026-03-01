import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def setup_neo4j():
    with open('ast_prerequisites.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    driver = GraphDatabase.driver(URI, auth=AUTH)

    def build_graph(tx, course_data):
        print("Clearing database...")
        tx.run("MATCH (n) DETACH DELETE n")

        print("Creating Course nodes...")
        for course_id, info in course_data.items():
            name = info.get('course_name', '').strip()
            semesters = info.get('semesters', [])
            tx.run("""
                MERGE (c:Course {id: $id})
                SET c.name = $name,
                    c.semesters = $semesters
            """, id=course_id, name=name, semesters=semesters)

        print("Traversing AST and creating Logic Nodes...")
        
        # Helper to recursively build the Logic graph
        def process_ast(ast, course_id, req_type, parent_id=None):
            if not ast: return
            
            # Base case: A direct course reference
            if ast.get("type") == "COURSE":
                target_id = ast.get("id")
                # Ensure the target course node exists
                tx.run("MERGE (c:Course {id: $id})", id=target_id)
                
                if parent_id:
                    # Link parent LogicNode to this Course
                    tx.run("""
                        MATCH (parent:LogicGroup {id: $parent_id}), (c:Course {id: $target_id})
                        MERGE (parent)-[:HAS_OPERAND]->(c)
                    """, parent_id=parent_id, target_id=target_id)
                else:
                    # Direct link from course to course (no logic group needed)
                    tx.run("""
                        MATCH (src:Course {id: $course_id}), (c:Course {id: $target_id})
                        MERGE (src)-[:HAS_PREREQUISITE {type: $req_type}]->(c)
                    """, course_id=course_id, target_id=target_id, req_type=req_type)
                return

            # Complex case: Logic Group (AND, OR, AT_LEAST_X)
            logic_type = ast.get("type")
            operands = ast.get("operands", [])
            
            # Create a unique ID for the logic group based on the course and a random or counter (we'll just use a hash or pseudo-random)
            import uuid
            logic_id = f"logic_{uuid.uuid4().hex[:8]}"
            
            tx.run("""
                CREATE (lg:LogicGroup {id: $logic_id, type: $logic_type, req_type: $req_type})
            """, logic_id=logic_id, logic_type=logic_type, req_type=req_type)
            
            # Link to parent (either the root course or a parent logic group)
            if parent_id:
                tx.run("""
                    MATCH (parent:LogicGroup {id: $parent_id}), (lg:LogicGroup {id: $logic_id})
                    MERGE (parent)-[:HAS_OPERAND]->(lg)
                """, parent_id=parent_id, logic_id=logic_id)
            else:
                tx.run("""
                    MATCH (src:Course {id: $course_id}), (lg:LogicGroup {id: $logic_id})
                    MERGE (src)-[:HAS_PREREQUISITE {type: $req_type}]->(lg)
                """, course_id=course_id, logic_id=logic_id, req_type=req_type)

            # Recurse for children
            for op in operands:
                process_ast(op, course_id, req_type, parent_id=logic_id)

        for course_id, info in course_data.items():
            reqs = info.get("requirements", {})
            for req_type in ["kabala", "darush", "mumlats"]:
                ast = reqs.get(req_type)
                if ast:
                    process_ast(ast, course_id, req_type)

    with driver.session() as session:
        try:
            session.execute_write(build_graph, data)
            print("Successfully populated Neo4j database.")
        except Exception as e:
            print(f"Error populating Neo4j: {e}")
            print("\\nPlease ensure Neo4j is running via Docker:")
            print("docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j")

    driver.close()

if __name__ == "__main__":
    setup_neo4j()
