### AI Prompt: Architecting a Constraint-Aware Topological Sort for Academic Planning

**Objective:**
Design a robust algorithm for an academic degree planner. The goal is to generate an optimal, semester-by-semester course sequence that satisfies all degree requirements in the shortest time possible while balancing workload and handling complex course relationships.

---

### 1. Data Model & Inputs
The algorithm must process four primary data structures:
1.  **Course Catalog:** Metadata including Course ID, Name, Credits, Level (Introductory, Intermediate, Advanced), and typical Semester availability (Fall, Spring, Summer).
2.  **Prerequisite AST (Abstract Syntax Tree):** A recursive structure for each course defining its requirements using `AND`, `OR`, and `MIN_CREDITS` logic. 
    *   *Example:* `Course C` requires `(Course A OR Course B) AND (18 total credits)`.
3.  **Overlap Registry:** A list of course sets that "overlap." If a student takes multiple courses in an overlap set, the total credits earned is less than the sum of individual credits (e.g., taking both *Calculus A* and *Infinitesimal Calculus 1*).
4.  **Degree Requirements:**
    *   **Mandatory:** Must take these specific courses.
    *   **Elective Groups:** "Choose X credits from list Y" or "Choose 2 courses from list Z."

---

### 2. Core Algorithm: The "Weighted Constraint-Topological Sort"
The algorithm should be an evolution of a standard Topological Sort (Kahn's or DFS-based), modified to handle non-linear dependencies.

#### A. Preprocessing & State Management
*   **Equivalence Mapping:** Identify "Equivalence Sets" based on overlaps. If `Course A` and `Course B` overlap significantly, the algorithm should treat them as potential substitutes in the dependency graph.
*   **Unlocked Potential (The Bottleneck Metric):** For every course, calculate its "Successor Weight"—the total number of future courses it unlocks (directly or indirectly) through the prerequisite tree.

#### B. The Optimization Loop
In each "Semester" iteration, the algorithm must select a set of `N` courses to "take" based on the following priorities:

1.  **Prerequisite Fulfillment (Hard Constraint):** Only consider courses whose `AND/OR` AST evaluates to `True` based on currently "completed" courses.
2.  **Heuristic Weighting (Selection Logic):**
    *   **Critical Path:** Prioritize courses with the highest "Successor Weight" (bottleneck courses).
    *   **Overlap Optimization:** If `Course A` and `Course B` overlap:
        *   Does taking `A` satisfy a degree requirement that `B` does not?
        *   Does `A` unlock a more critical path than `B`?
        *   *Substitution Logic:* If a student has already taken `Infinitesimal 1 + 2`, automatically "mark as satisfied" the requirement for `Calculus A`, and prune `Calculus A` from future planning.
    *   **OR-Logic Branching:** If a requirement is `(A OR B)`, evaluate which branch leads to a more efficient path (e.g., `A` might be a prerequisite for a future elective the user wants, while `B` is a dead end).
3.  **Workload Balancing (Soft Constraint):**
    *   Assign a "Difficulty Score" to courses.
    *   Ensure the sum of credits and difficulty scores in a single semester does not exceed a user-defined threshold.
4.  **Temporal Constraint:** Only schedule a course if it is offered in the current semester (Fall/Spring/Summer).

---

### 3. Advanced Features to Implement
*   **Greedy vs. Global Optimization:** Explain how to use a **Backtracking Search** or **A* Search** to find the absolute shortest path to graduation, rather than just picking the "best" courses for the next semester.
*   **User-in-the-Loop:** How should the algorithm react if a user "pins" a specific course to a specific semester? It must re-validate the entire future path and flag any prerequisite violations.
*   **Credit Max-Minimization:** In degrees with elective groups, the algorithm should prioritize courses that satisfy *multiple* requirements simultaneously (e.g., a course that counts as both a "Computer Science Elective" and an "Advanced Credit" requirement).

---

### 4. Output Requirements
The algorithm should return:
1.  **The Schedule:** A list of semesters, each containing a list of Course IDs.
2.  **The Rationale:** For each choice, a brief "why" (e.g., "Critical bottleneck for 4 future courses," "Optimal substitute for Calculus A").
3.  **Warning Flags:** Any potential issues, such as "High workload in Semester 3" or "Course X only offered once every 2 years."

---

**Guidance for the AI:** 
Focus on the **Graph Theory** aspect. Treat the degree as a Directed Acyclic Graph (DAG) where some nodes are "Alternative" nodes (OR logic) and some nodes have "Inhibition" edges (Overlaps). Use a priority queue to manage the "ready" set of courses during the sort.
