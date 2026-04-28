# CS348 Stage 3 - Student Management System

## Project Overview
A full-stack Student Management System demonstrating database concepts:
- **Backend:** Flask (Python) with SQLite
- **Frontend:** React

## Stage 3 Deliverables Implementation

### 1. SQL Injection Protection (9% of project grade)

#### Method 1: Parameterized Queries (Prepared Statements)
All database queries use parameterized statements with `?` placeholders. User input is NEVER concatenated directly into SQL strings.

**Location in code:** `app.py` - All route handlers

```python
# SAFE - Parameterized query (what we use)
cursor.execute(
    "INSERT INTO students (name, age, gpa, course_id) VALUES (?, ?, ?, ?)",
    (name, age, gpa, course_id)
)

# UNSAFE - String concatenation
# cursor.execute(f"INSERT INTO students (name) VALUES ('{name}')")
```

**Examples in the application:**
- `add_student()` - Lines 270-273
- `delete_student()` - Line 295
- `update_student()` - Lines 330-335
- `filter_students()` - Lines 390-395

#### Method 2: Input Validation & Sanitization
**Location in code:** `app.py` - Lines 40-78

```python
def sanitize_string(value, max_length=100):
    """Sanitize string input - removes dangerous characters"""
    value = str(value).strip()[:max_length]
    value = re.sub(r'[<>"\';\\]', '', value)  # Remove SQL/XSS characters
    return value

def validate_integer(value, min_val=None, max_val=None):
    """Validate integer with range checking"""
    int_val = int(value)
    if min_val and int_val < min_val: raise ValueError()
    return int_val

def validate_float(value, min_val=None, max_val=None):
    """Validate float (GPA) with range checking"""
    # Similar to validate_integer but for floats
```

---

### 2. Database Indexes (8% of project grade)

**Location in code:** `app.py` - `init_db()` function, Lines 120-155

#### Index 1: `idx_students_age`
```sql
CREATE INDEX IF NOT EXISTS idx_students_age ON students(age)
```
- **Query benefited:** Filter Students report - age range filtering
- **SQL:** `WHERE s.age >= ? AND s.age <= ?`
- **Feature:** Filter students by age range in the Students tab
- **Justification:** Age range queries are common in student filtering. Without this index, SQLite would do a full table scan. With the index, it performs a fast B-tree range scan.

#### Index 2: `idx_students_gpa`
```sql
CREATE INDEX IF NOT EXISTS idx_students_gpa ON students(gpa)
```
- **Query benefited:** Filter Students report - GPA range filtering
- **SQL:** `WHERE s.gpa >= ? AND s.gpa <= ?`
- **Feature:** Filter students by GPA range in the Students tab
- **Justification:** GPA filtering is a critical feature for academic reports. Index enables efficient range queries on GPA values.

#### Index 3: `idx_students_course_id`
```sql
CREATE INDEX IF NOT EXISTS idx_students_course_id ON students(course_id)
```
- **Query benefited:** 
  - Filter by course: `WHERE s.course_id = ?`
  - JOIN operations: `LEFT JOIN courses c ON s.course_id = c.id`
- **Feature:** Course-based filtering and student-course JOINs
- **Justification:** Foreign key lookups and JOINs benefit significantly from indexes. This index speeds up both course filtering and the JOIN used in almost every student query.

#### Index 4: `idx_students_age_gpa` (Composite Index)
```sql
CREATE INDEX IF NOT EXISTS idx_students_age_gpa ON students(age, gpa)
```
- **Query benefited:** Combined age AND GPA filtering
- **SQL:** `WHERE s.age >= ? AND s.age <= ? AND s.gpa >= ? AND s.gpa <= ?`
- **Feature:** Advanced filtering combining age and GPA criteria
- **Justification:** When users filter by both age AND GPA simultaneously, SQLite can use this single composite index instead of scanning two separate indexes and intersecting results.

#### Verifying Index Usage
Use the "Database" tab in the UI or call the API:
```
GET /db/explain/age_filter
GET /db/explain/gpa_filter
GET /db/explain/course_filter
GET /db/explain/combined
GET /db/explain/join
```

---

### 3. Transactions and Isolation Levels (8% of project grade)

**Location in code:** `app.py`

#### Transaction Implementation

All write operations (INSERT, UPDATE, DELETE) are wrapped in explicit transactions:

```python
conn = get_conn(isolation_level='IMMEDIATE')
try:
    cursor.execute("INSERT INTO students ...", params)
    conn.commit()  # Success - make changes permanent
except sqlite3.Error as e:
    conn.rollback()  # Error - undo all changes
finally:
    conn.close()
```

#### Isolation Level: IMMEDIATE

**Why IMMEDIATE?**

SQLite supports these isolation levels:
- `DEFERRED` (default) - Locks acquired on first read/write
- `IMMEDIATE` - Write lock acquired at transaction start
- `EXCLUSIVE` - Exclusive lock preventing all other access

We chose **IMMEDIATE** because:

1. **Prevents Dirty Reads:** Other transactions cannot read uncommitted data
2. **Prevents Lost Updates:** Acquires write lock immediately, so concurrent transactions must wait
3. **Good for Multi-User Web Apps:** Allows readers but serializes writers
4. **Avoids Deadlocks:** Acquiring lock early prevents circular wait conditions

**Code location:** `app.py` - `get_conn()` function, Line 85

```python
def get_conn(isolation_level=None):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    if isolation_level is not None:
        conn.isolation_level = isolation_level
    return conn
```

#### Transaction Examples

**1. Batch Add Students** (`/students/batch` - Lines 440-485)
- Adds multiple students in a single transaction
- If ANY insert fails, ALL are rolled back
- Demonstrates atomicity

**2. Transfer Students** (`/students/transfer` - Lines 490-540)
- Moves all students from one course to another
- Demonstrates multi-record atomic update
- Rollback ensures no partial transfers

**Demo in UI:** Navigate to "Transactions" tab to test these features.

---

## Running the Application

### Backend (Flask)
```bash
cd /Users/simrithranjan/cs348/stage1
source venv/bin/activate
python app.py
```
Backend runs on: http://127.0.0.1:5000

### Frontend (React)
```bash
cd /Users/simrithranjan/cs348/stage1/client
npm start
```
Frontend runs on: http://localhost:3000

---

## API Endpoints

| Method | Endpoint | Description | Stage 3 Features |
|--------|----------|-------------|------------------|
| GET | `/students` | Get all students | Parameterized query, uses idx_students_course_id |
| POST | `/students` | Add a student | Input sanitization, parameterized query, IMMEDIATE transaction |
| PUT | `/students/<id>` | Update a student | Input validation, parameterized query, IMMEDIATE transaction |
| DELETE | `/students/<id>` | Delete a student | Integer validation, parameterized query, IMMEDIATE transaction |
| GET | `/students/filter` | Filter students | Uses all indexes, parameterized dynamic query |
| GET | `/courses` | Get all courses | Parameterized query |
| POST | `/courses` | Add a course | Input sanitization, IMMEDIATE transaction |
| POST | `/students/batch` | Batch add students | Transaction with rollback demo |
| POST | `/students/transfer` | Transfer students | Multi-record transaction demo |
| GET | `/db/info` | Get schema & indexes | Shows all created indexes |
| GET | `/db/explain/<type>` | Query execution plan | Demonstrates index usage |

---

## Demo Script for Stage 3

### SQL Injection Protection Demo
1. Go to "Students" tab
2. Try adding a student with malicious input like `'; DROP TABLE students; --` as the name
3. Show that:
   - Input is sanitized (dangerous characters removed)
   - Parameterized query prevents execution of malicious SQL
   - Show `app.py` code: `sanitize_string()` and parameterized queries

### Indexes Demo
1. Go to "Database" tab
2. Click "Load Database Info"
3. Show the 4 indexes created
4. Click each "Query Plan" button to show SQLite using indexes
5. Explain why each index is meaningful for the application

### Transactions Demo
1. Go to "Transactions" tab
2. **Batch Add:**
   - Add multiple students via JSON
   - Show all-or-nothing behavior
   - Intentionally add invalid data to show rollback
3. **Transfer Students:**
   - Transfer students between courses
   - Show atomic update of multiple records
4. Show code in `app.py` explaining IMMEDIATE isolation level choice

---

## File Structure
```
stage1/
├── app.py                 # Flask backend with Stage 3 implementations
├── students.db            # SQLite database
├── STAGE3_README.md       # This documentation
├── client/
│   ├── src/
│   │   └── App.js         # React frontend
│   └── package.json
└── venv/                  # Python virtual environment
```

