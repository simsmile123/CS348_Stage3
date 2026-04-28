"""
CS348 Stage 3 - Student Management System Backend
=================================================

STAGE 3 IMPLEMENTATION DETAILS:
-------------------------------

1. SQL INJECTION PROTECTION:
   - All database queries use PARAMETERIZED QUERIES (prepared statements) with ? placeholders
   - User input is validated and sanitized before database operations
   - Input validation includes type checking, range validation, and sanitization

2. DATABASE INDEXES:
   - idx_students_age: Supports age range filtering in the Filter Students report
   - idx_students_gpa: Supports GPA range filtering in the Filter Students report  
   - idx_students_course_id: Supports course-based filtering and JOIN operations
   - idx_students_age_gpa: Composite index for combined age+GPA range queries

3. TRANSACTIONS AND ISOLATION LEVELS:
   - All write operations (INSERT, UPDATE, DELETE) are wrapped in explicit transactions
   - Using IMMEDIATE isolation level for write operations to prevent dirty reads
   - Batch operations demonstrate transaction rollback on failure
   - Connection management ensures proper commit/rollback handling
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import re

app = Flask(__name__, static_folder="client/build", static_url_path="/")
CORS(app)

DB_FILE = os.environ.get("DB_FILE", "students.db")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "client", "build")

def _react_build_exists() -> bool:
    return os.path.isdir(STATIC_DIR) and os.path.isfile(os.path.join(STATIC_DIR, "index.html"))

# ============================================================================
# STAGE 3 REQUIREMENT 1: SQL INJECTION PROTECTION - INPUT SANITIZATION
# ============================================================================
def sanitize_string(value, max_length=100):
    """
    Sanitize string input to prevent SQL injection and XSS attacks.
    - Removes potentially dangerous characters
    - Limits string length
    - Strips leading/trailing whitespace
    """
    if value is None:
        return None
    # Convert to string and strip whitespace
    value = str(value).strip()
    # Limit length to prevent buffer overflow attacks
    value = value[:max_length]
    # Remove or escape potentially dangerous characters
    # Note: This is a secondary defense - parameterized queries are primary protection
    value = re.sub(r'[<>"\';\\]', '', value)
    return value

def validate_integer(value, min_val=None, max_val=None):
    """
    Validate and sanitize integer input.
    - Ensures value is a valid integer
    - Optionally checks range bounds
    """
    if value is None or value == '':
        return None
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            raise ValueError(f"Value must be >= {min_val}")
        if max_val is not None and int_val > max_val:
            raise ValueError(f"Value must be <= {max_val}")
        return int_val
    except (ValueError, TypeError):
        raise ValueError(f"Invalid integer value: {value}")

def validate_float(value, min_val=None, max_val=None):
    """
    Validate and sanitize float input (e.g., GPA).
    - Ensures value is a valid float
    - Optionally checks range bounds
    """
    if value is None or value == '':
        return None
    try:
        float_val = float(value)
        if min_val is not None and float_val < min_val:
            raise ValueError(f"Value must be >= {min_val}")
        if max_val is not None and float_val > max_val:
            raise ValueError(f"Value must be <= {max_val}")
        return float_val
    except (ValueError, TypeError):
        raise ValueError(f"Invalid float value: {value}")


# ============================================================================
# DATABASE CONNECTION WITH TRANSACTION SUPPORT
# ============================================================================
def get_conn(isolation_level=None):
    """
    Get database connection with specified isolation level.
    
    STAGE 3 REQUIREMENT 3: ISOLATION LEVELS
    ---------------------------------------
    SQLite supports the following isolation levels:
    - None (autocommit mode)
    - '' (default - DEFERRED)
    - 'DEFERRED' - Locks acquired when first read/write
    - 'IMMEDIATE' - Write lock acquired immediately (prevents other writers)
    - 'EXCLUSIVE' - Exclusive lock (prevents all other access)
    
    For this application:
    - Read operations use default (DEFERRED) for better concurrency
    - Write operations use IMMEDIATE to prevent dirty reads/writes
    """
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    if isolation_level is not None:
        conn.isolation_level = isolation_level
    return conn


# ============================================================================
# STAGE 3 REQUIREMENT 2: DATABASE INDEXES
# ============================================================================
def init_db():
    """
    Initialize database with tables and indexes.
    
    INDEX JUSTIFICATION:
    -------------------
    1. idx_students_age: 
       - Used by: Filter Students report (age range queries)
       - Query: WHERE s.age >= ? AND s.age <= ?
       - Benefit: Fast range scans for age-based filtering
    
    2. idx_students_gpa:
       - Used by: Filter Students report (GPA range queries)
       - Query: WHERE s.gpa >= ? AND s.gpa <= ?
       - Benefit: Fast range scans for GPA-based filtering
    
    3. idx_students_course_id:
       - Used by: Filter Students report, JOIN operations
       - Query: WHERE s.course_id = ?, JOIN courses c ON s.course_id = c.id
       - Benefit: Fast lookup for course filtering, efficient JOINs
    
    4. idx_students_age_gpa (Composite Index):
       - Used by: Filter Students report (combined age+GPA filtering)
       - Query: WHERE s.age >= ? AND s.age <= ? AND s.gpa >= ? AND s.gpa <= ?
       - Benefit: Single index scan for combined filter conditions
    """
    conn = get_conn(isolation_level='IMMEDIATE')
    c = conn.cursor()
    
    try:
        # ---- TABLE CREATION ----
        # Courses table
        c.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Students table with foreign key
        c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age > 0 AND age < 150),
                gpa REAL NOT NULL CHECK(gpa >= 0.0 AND gpa <= 4.0),
                course_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL
            )
        """)

        # ---- INDEX CREATION (STAGE 3 REQUIREMENT 2) ----
        
        # Index 1: Age-based filtering for Filter Students report
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_age 
            ON students(age)
        """)
        
        # Index 2: GPA-based filtering for Filter Students report
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_gpa 
            ON students(gpa)
        """)
        
        # Index 3: Course filtering and JOIN optimization
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_course_id 
            ON students(course_id)
        """)
        
        # Index 4: Composite index for combined age+GPA filtering
        # This index is particularly useful when both age AND GPA filters are applied
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_students_age_gpa 
            ON students(age, gpa)
        """)

        # Preload courses if empty
        c.execute("SELECT COUNT(*) FROM courses")
        if c.fetchone()[0] == 0:
            # Using parameterized queries even for seed data (SQL injection protection)
            courses = [("Database Systems",), ("AI Fundamentals",), ("Web Development",), 
                      ("Machine Learning",), ("Computer Networks",)]
            c.executemany("INSERT INTO courses (name) VALUES (?)", courses)
        
        conn.commit()
        print("Database initialized successfully with indexes.")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


init_db()


# ============================================================================
# STAGE 3 REQUIREMENT 3: TRANSACTION WRAPPER
# ============================================================================
def execute_in_transaction(operations, isolation_level='IMMEDIATE'):
    """
    Execute multiple database operations within a single transaction.
    
    TRANSACTION HANDLING:
    --------------------
    - All operations succeed together or fail together (atomicity)
    - Uses specified isolation level for concurrency control
    - Automatic rollback on any error
    
    ISOLATION LEVEL CHOICE: IMMEDIATE
    ---------------------------------
    We use IMMEDIATE because:
    1. Prevents other transactions from writing while we're in progress
    2. Avoids dirty reads (reading uncommitted data)
    3. Suitable for a multi-user web application
    4. Balances consistency with reasonable performance
    
    For a read-heavy application, DEFERRED could be used for reads
    to allow more concurrency.
    
    Args:
        operations: List of (sql, params) tuples to execute
        isolation_level: SQLite isolation level
    
    Returns:
        List of results from each operation
    """
    conn = get_conn(isolation_level=isolation_level)
    cursor = conn.cursor()
    results = []
    
    try:
        for sql, params in operations:
            cursor.execute(sql, params)
            results.append({
                'rowcount': cursor.rowcount,
                'lastrowid': cursor.lastrowid
            })
        
        # COMMIT: All operations succeeded, make changes permanent
        conn.commit()
        return results
        
    except sqlite3.Error as e:
        # ROLLBACK: An error occurred, undo all changes
        conn.rollback()
        raise Exception(f"Transaction failed, rolled back: {str(e)}")
    finally:
        conn.close()


# ============================================================================
# API ROUTES
# ============================================================================

@app.route("/students", methods=["GET"])
def get_students():
    """
    Get all students with course information.
    
    SQL INJECTION PROTECTION: No user input used in this query.
    INDEX USED: idx_students_course_id (for JOIN optimization)
    """
    conn = get_conn()
    try:
        # Parameterized query (no user input, but demonstrates pattern)
        rows = conn.execute("""
            SELECT s.id, s.name, s.age, s.gpa, c.name AS course_name, s.course_id
            FROM students s
            LEFT JOIN courses c ON s.course_id = c.id
            ORDER BY s.name
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/students", methods=["POST"])
def add_student():
    """
    Add a new student.
    
    SQL INJECTION PROTECTION:
    1. Input validation (sanitize_string, validate_integer, validate_float)
    2. Parameterized query with ? placeholders
    
    TRANSACTION: Uses IMMEDIATE isolation level to ensure atomicity
    """
    data = request.json
    
    # INPUT VALIDATION AND SANITIZATION (Stage 3 Requirement 1)
    try:
        name = sanitize_string(data.get("name"), max_length=100)
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        age = validate_integer(data.get("age"), min_val=1, max_val=150)
        if age is None:
            return jsonify({"error": "Valid age is required"}), 400
        
        gpa = validate_float(data.get("gpa"), min_val=0.0, max_val=4.0)
        if gpa is None:
            return jsonify({"error": "Valid GPA (0.0-4.0) is required"}), 400
        
        course_id = validate_integer(data.get("course_id"))
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    # TRANSACTION WITH PARAMETERIZED QUERY (Stage 3 Requirements 1 & 3)
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        # Parameterized query prevents SQL injection
        cursor = conn.execute(
            "INSERT INTO students (name, age, gpa, course_id) VALUES (?, ?, ?, ?)",
            (name, age, gpa, course_id)
        )
        student_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": "Student added", "id": student_id}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    """
    Delete a student by ID.
    
    SQL INJECTION PROTECTION:
    1. Flask route converter <int:id> ensures id is integer
    2. Parameterized query with ? placeholder
    
    TRANSACTION: Uses IMMEDIATE isolation level
    """
    # Validate ID (additional protection beyond Flask's int converter)
    try:
        student_id = validate_integer(id, min_val=1)
    except ValueError:
        return jsonify({"error": "Invalid student ID"}), 400
    
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        # Parameterized DELETE query
        cursor = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Student not found"}), 404
        conn.commit()
        return jsonify({"message": "Student deleted successfully"})
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/students/<int:id>", methods=["PUT"])
def update_student(id):
    """
    Update a student's information.
    
    SQL INJECTION PROTECTION:
    1. Flask route converter <int:id> ensures id is integer
    2. All input validated and sanitized
    3. Parameterized query with ? placeholders
    
    TRANSACTION: Uses IMMEDIATE isolation level for atomic update
    """
    data = request.json
    
    # INPUT VALIDATION AND SANITIZATION
    try:
        student_id = validate_integer(id, min_val=1)
        name = sanitize_string(data.get("name"), max_length=100)
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        age = validate_integer(data.get("age"), min_val=1, max_val=150)
        if age is None:
            return jsonify({"error": "Valid age is required"}), 400
        
        gpa = validate_float(data.get("gpa"), min_val=0.0, max_val=4.0)
        if gpa is None:
            return jsonify({"error": "Valid GPA (0.0-4.0) is required"}), 400
        
        course_id = validate_integer(data.get("course_id"))
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        # Parameterized UPDATE query
        cursor = conn.execute(
            """UPDATE students 
               SET name=?, age=?, gpa=?, course_id=?, updated_at=CURRENT_TIMESTAMP 
               WHERE id=?""",
            (name, age, gpa, course_id, student_id)
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Student not found"}), 404
        conn.commit()
        return jsonify({"message": "Student updated successfully"})
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/students/filter", methods=["GET"])
def filter_students():
    """
    Filter students by age range, GPA range, and/or course.
    
    SQL INJECTION PROTECTION:
    1. All filter parameters validated
    2. Query built with parameterized placeholders (?)
    3. No string concatenation of user input into SQL
    
    INDEXES USED:
    - idx_students_age: When filtering by age range
    - idx_students_gpa: When filtering by GPA range
    - idx_students_age_gpa: When filtering by both age AND GPA
    - idx_students_course_id: When filtering by course
    """
    params = request.args
    
    # INPUT VALIDATION (Stage 3 Requirement 1)
    try:
        age_min = validate_integer(params.get("ageMin"), min_val=0, max_val=150)
        age_max = validate_integer(params.get("ageMax"), min_val=0, max_val=150)
        gpa_min = validate_float(params.get("gpaMin"), min_val=0.0, max_val=4.0)
        gpa_max = validate_float(params.get("gpaMax"), min_val=0.0, max_val=4.0)
        course_id = validate_integer(params.get("courseId"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    # BUILD PARAMETERIZED QUERY (Stage 3 Requirement 1)
    # Note: We NEVER concatenate user input directly into SQL
    query = """
        SELECT s.id, s.name, s.age, s.gpa, c.name AS course_name, s.course_id
        FROM students s
        LEFT JOIN courses c ON s.course_id = c.id
        WHERE 1=1
    """
    args = []
    
    # Each condition uses ? placeholder - NEVER string formatting
    if age_min is not None:
        query += " AND s.age >= ?"
        args.append(age_min)
    if age_max is not None:
        query += " AND s.age <= ?"
        args.append(age_max)
    if gpa_min is not None:
        query += " AND s.gpa >= ?"
        args.append(gpa_min)
    if gpa_max is not None:
        query += " AND s.gpa <= ?"
        args.append(gpa_max)
    if course_id is not None:
        query += " AND s.course_id = ?"
        args.append(course_id)
    
    query += " ORDER BY s.name"
    
    conn = get_conn()
    try:
        # Execute parameterized query - args passed separately from SQL
        rows = conn.execute(query, args).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/courses", methods=["GET"])
def get_courses():
    """
    Get all available courses (used to populate dropdowns dynamically).
    
    SQL INJECTION PROTECTION: No user input in this query.
    """
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM courses ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/courses", methods=["POST"])
def add_course():
    """
    Add a new course.
    
    SQL INJECTION PROTECTION:
    1. Input sanitization for course name
    2. Parameterized INSERT query
    
    TRANSACTION: IMMEDIATE isolation level
    """
    data = request.json
    
    try:
        name = sanitize_string(data.get("name"), max_length=100)
        if not name:
            return jsonify({"error": "Course name is required"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        cursor = conn.execute(
            "INSERT INTO courses (name) VALUES (?)",
            (name,)
        )
        course_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": "Course added", "id": course_id}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"error": "Course already exists"}), 400
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()


# ============================================================================
# STAGE 3: BATCH OPERATIONS WITH TRANSACTIONS
# ============================================================================

@app.route("/students/batch", methods=["POST"])
def batch_add_students():
    """
    Add multiple students in a single transaction.
    
    TRANSACTION DEMONSTRATION:
    - All students are added within ONE transaction
    - If ANY student fails validation or insert, ALL are rolled back
    - This ensures data consistency (atomicity)
    
    ISOLATION LEVEL: IMMEDIATE
    - Prevents other writes during the batch operation
    - Ensures no other transaction can see partial results
    """
    data = request.json
    students = data.get("students", [])
    
    if not students:
        return jsonify({"error": "No students provided"}), 400

    # Execute validation + inserts inside ONE transaction so rollback is visible
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        cursor = conn.cursor()
        inserted_ids = []

        for i, student in enumerate(students):
            # Validate each row; if any row is invalid after prior inserts,
            # we roll back the entire transaction (atomicity demo).
            try:
                validated = {
                    "name": sanitize_string(student.get("name"), max_length=100),
                    "age": validate_integer(student.get("age"), min_val=1, max_val=150),
                    "gpa": validate_float(student.get("gpa"), min_val=0.0, max_val=4.0),
                    "course_id": validate_integer(student.get("course_id")),
                }
            except ValueError as e:
                raise ValueError(f"Validation error for student {i+1}: {str(e)}") from e

            if not validated["name"] or validated["age"] is None or validated["gpa"] is None:
                raise ValueError(f"Invalid data for student {i+1}")

            cursor.execute(
                "INSERT INTO students (name, age, gpa, course_id) VALUES (?, ?, ?, ?)",
                (validated["name"], validated["age"], validated["gpa"], validated["course_id"])
            )
            inserted_ids.append(cursor.lastrowid)
        
        # All inserts succeeded - commit the transaction
        conn.commit()
        return jsonify({
            "message": f"Successfully added {len(inserted_ids)} students",
            "ids": inserted_ids
        }), 201

    except ValueError as e:
        conn.rollback()
        return jsonify({"error": f"Transaction rolled back: {str(e)}"}), 400
    except sqlite3.Error as e:
        # Any error - rollback ALL inserts
        conn.rollback()
        return jsonify({"error": f"Transaction rolled back: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/students/transfer", methods=["POST"])
def transfer_students():
    """
    Transfer students from one course to another.
    
    TRANSACTION DEMONSTRATION (Multi-table operation):
    - Updates multiple student records atomically
    - Demonstrates IMMEDIATE isolation preventing concurrent modifications
    
    This is an example of where transactions are critical:
    - Without transactions, a crash mid-transfer could leave data inconsistent
    - With transactions, either ALL transfers complete or NONE do
    """
    data = request.json
    
    try:
        from_course_id = validate_integer(data.get("from_course_id"))
        to_course_id = validate_integer(data.get("to_course_id"))
        
        if from_course_id is None or to_course_id is None:
            return jsonify({"error": "Both course IDs are required"}), 400
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    conn = get_conn(isolation_level='IMMEDIATE')
    try:
        # First, verify both courses exist
        from_course = conn.execute(
            "SELECT id FROM courses WHERE id = ?", (from_course_id,)
        ).fetchone()
        to_course = conn.execute(
            "SELECT id FROM courses WHERE id = ?", (to_course_id,)
        ).fetchone()
        
        if not from_course:
            return jsonify({"error": "Source course not found"}), 404
        if not to_course:
            return jsonify({"error": "Destination course not found"}), 404
        
        # Perform the transfer
        cursor = conn.execute(
            "UPDATE students SET course_id = ?, updated_at = CURRENT_TIMESTAMP WHERE course_id = ?",
            (to_course_id, from_course_id)
        )
        
        transferred_count = cursor.rowcount
        conn.commit()
        
        return jsonify({
            "message": f"Successfully transferred {transferred_count} students",
            "from_course_id": from_course_id,
            "to_course_id": to_course_id
        })
        
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Transfer failed, rolled back: {str(e)}"}), 500
    finally:
        conn.close()


# ============================================================================
# DATABASE INFO ENDPOINT (for demo purposes)
# ============================================================================

@app.route("/db/info", methods=["GET"])
def get_db_info():
    """
    Get database schema information including indexes.
    Useful for demonstrating Stage 3 index implementation.
    """
    conn = get_conn()
    try:
        # Get all indexes
        indexes = conn.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type = 'index' AND sql IS NOT NULL
            ORDER BY tbl_name, name
        """).fetchall()
        
        # Get table info
        tables = conn.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        return jsonify({
            "indexes": [{"name": idx["name"], "table": idx["tbl_name"], "sql": idx["sql"]} 
                       for idx in indexes],
            "tables": [{"name": tbl["name"], "sql": tbl["sql"]} for tbl in tables]
        })
    finally:
        conn.close()


@app.route("/db/explain/<query_type>", methods=["GET"])
def explain_query(query_type):
    """
    Show query execution plan to demonstrate index usage.
    
    This endpoint shows how SQLite uses indexes for different queries.
    Useful for Stage 3 demo to prove indexes are being used.
    """
    conn = get_conn()
    try:
        plans = {}
        
        if query_type == "age_filter":
            # Demonstrates idx_students_age usage
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM students WHERE age >= 18 AND age <= 25"
            ).fetchall()
            plans["age_filter"] = [dict(p) for p in plan]
            
        elif query_type == "gpa_filter":
            # Demonstrates idx_students_gpa usage
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM students WHERE gpa >= 3.0 AND gpa <= 4.0"
            ).fetchall()
            plans["gpa_filter"] = [dict(p) for p in plan]
            
        elif query_type == "course_filter":
            # Demonstrates idx_students_course_id usage
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM students WHERE course_id = 1"
            ).fetchall()
            plans["course_filter"] = [dict(p) for p in plan]
            
        elif query_type == "combined":
            # Demonstrates composite index usage
            plan = conn.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM students WHERE age >= 18 AND age <= 25 AND gpa >= 3.0"
            ).fetchall()
            plans["combined_filter"] = [dict(p) for p in plan]
            
        elif query_type == "join":
            # Demonstrates idx_students_course_id for JOIN
            plan = conn.execute(
                """EXPLAIN QUERY PLAN 
                   SELECT s.*, c.name 
                   FROM students s 
                   JOIN courses c ON s.course_id = c.id"""
            ).fetchall()
            plans["join"] = [dict(p) for p in plan]
        else:
            return jsonify({"error": "Unknown query type. Use: age_filter, gpa_filter, course_filter, combined, join"}), 400
            
        return jsonify(plans)
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# React SPA static serving (must be defined AFTER API routes)
# ----------------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """
    Serve the built React app in production.
    This handler is defined after API routes so it does not intercept them.
    """
    if not _react_build_exists():
        return jsonify(
            {
                "message": "React build not found. Run `npm run build` in stage1/client.",
            }
        ), 404

    requested_path = os.path.join(STATIC_DIR, path)
    if path and os.path.isfile(requested_path):
        return send_from_directory(STATIC_DIR, path)

    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
