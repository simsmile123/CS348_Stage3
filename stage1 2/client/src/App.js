import React, { useState, useEffect } from "react";
import axios from "axios";

const apiBaseURL =
  process.env.NODE_ENV === "production" ? "" : "http://127.0.0.1:5000";
const api = axios.create({ baseURL: apiBaseURL });

// Styles
const styles = {
  container: {
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "20px",
    backgroundColor: "#f5f7fa",
    minHeight: "100vh",
  },
  header: {
    textAlign: "center",
    marginBottom: "30px",
    padding: "20px",
    backgroundColor: "#3498db",
    color: "white",
    borderRadius: "10px",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
  },
  section: {
    backgroundColor: "white",
    padding: "20px",
    marginBottom: "20px",
    borderRadius: "8px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  sectionTitle: {
    color: "#2c3e50",
    borderBottom: "2px solid #3498db",
    paddingBottom: "10px",
    marginBottom: "15px",
  },
  input: {
    padding: "10px",
    margin: "5px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
  },
  select: {
    padding: "10px",
    margin: "5px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "14px",
    minWidth: "150px",
  },
  button: {
    padding: "10px 20px",
    margin: "5px",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background-color 0.3s",
  },
  primaryButton: {
    backgroundColor: "#3498db",
    color: "white",
  },
  successButton: {
    backgroundColor: "#27ae60",
    color: "white",
  },
  dangerButton: {
    backgroundColor: "#e74c3c",
    color: "white",
  },
  warningButton: {
    backgroundColor: "#f39c12",
    color: "white",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "15px",
  },
  th: {
    backgroundColor: "#3498db",
    color: "white",
    padding: "12px",
    textAlign: "left",
    borderBottom: "2px solid #2980b9",
  },
  td: {
    padding: "12px",
    borderBottom: "1px solid #ddd",
  },
  tabs: {
    display: "flex",
    marginBottom: "20px",
    borderBottom: "2px solid #3498db",
  },
  tab: {
    padding: "10px 20px",
    cursor: "pointer",
    border: "none",
    backgroundColor: "transparent",
    fontSize: "16px",
    transition: "all 0.3s",
  },
  activeTab: {
    backgroundColor: "#3498db",
    color: "white",
    borderRadius: "4px 4px 0 0",
  },
  codeBlock: {
    backgroundColor: "#2c3e50",
    color: "#ecf0f1",
    padding: "15px",
    borderRadius: "4px",
    fontFamily: "monospace",
    fontSize: "12px",
    overflow: "auto",
    whiteSpace: "pre-wrap",
  },
  badge: {
    display: "inline-block",
    padding: "4px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    marginRight: "5px",
  },
};

function App() {
  const [activeTab, setActiveTab] = useState("students");
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [dbInfo, setDbInfo] = useState(null);
  const [queryPlan, setQueryPlan] = useState(null);
  const [filters, setFilters] = useState({
    ageMin: "",
    ageMax: "",
    gpaMin: "",
    gpaMax: "",
    courseId: "",
  });
  const [newStudent, setNewStudent] = useState({
    name: "",
    age: "",
    gpa: "",
    course_id: "",
  });
  const [editingStudent, setEditingStudent] = useState(null);
  const [newCourse, setNewCourse] = useState("");
  const [message, setMessage] = useState({ text: "", type: "" });
  const [batchStudents, setBatchStudents] = useState("");
  const [transfer, setTransfer] = useState({ from: "", to: "" });

  useEffect(() => {
    fetchStudents();
    fetchCourses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showMessage = (text, type = "success") => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: "", type: "" }), 3000);
  };

  const fetchStudents = async () => {
    try {
      const res = await api.get("/students");
      setStudents(res.data);
    } catch (err) {
      showMessage("Error fetching students", "error");
    }
  };

  const fetchCourses = async () => {
    try {
      const res = await api.get("/courses");
      setCourses(res.data);
    } catch (err) {
      showMessage("Error fetching courses", "error");
    }
  };

  const fetchDbInfo = async () => {
    try {
      const res = await api.get("/db/info");
      setDbInfo(res.data);
    } catch (err) {
      showMessage("Error fetching database info", "error");
    }
  };

  const fetchQueryPlan = async (queryType) => {
    try {
      const res = await api.get(`/db/explain/${queryType}`);
      setQueryPlan({ type: queryType, data: res.data });
    } catch (err) {
      showMessage("Error fetching query plan", "error");
    }
  };

  const addStudent = async () => {
    try {
      await api.post("/students", newStudent);
      setNewStudent({ name: "", age: "", gpa: "", course_id: "" });
      fetchStudents();
      showMessage("Student added successfully!");
    } catch (err) {
      showMessage(err.response?.data?.error || "Error adding student", "error");
    }
  };

  const deleteStudent = async (id) => {
    if (!window.confirm("Are you sure you want to delete this student?")) return;
    try {
      await api.delete(`/students/${id}`);
      setStudents((prev) => prev.filter((s) => s.id !== id));
      showMessage("Student deleted successfully!");
    } catch (err) {
      showMessage(err.response?.data?.error || "Error deleting student", "error");
    }
  };

  const startEdit = (s) => setEditingStudent({ ...s });

  const updateStudent = async () => {
    try {
      await api.put(`/students/${editingStudent.id}`, editingStudent);
      setEditingStudent(null);
      fetchStudents();
      showMessage("Student updated successfully!");
    } catch (err) {
      showMessage(err.response?.data?.error || "Error updating student", "error");
    }
  };

  const handleFilterChange = (e) =>
    setFilters({ ...filters, [e.target.name]: e.target.value });

  const applyFilter = async () => {
    try {
      const res = await api.get("/students/filter", { params: filters });
      setStudents(res.data);
      showMessage(`Found ${res.data.length} students matching filters`);
    } catch (err) {
      showMessage(err.response?.data?.error || "Error filtering students", "error");
    }
  };

  const clearFilters = () => {
    setFilters({ ageMin: "", ageMax: "", gpaMin: "", gpaMax: "", courseId: "" });
    fetchStudents();
  };

  const addCourse = async () => {
    if (!newCourse.trim()) return;
    try {
      await api.post("/courses", { name: newCourse });
      setNewCourse("");
      fetchCourses();
      showMessage("Course added successfully!");
    } catch (err) {
      showMessage(err.response?.data?.error || "Error adding course", "error");
    }
  };

  const batchAddStudents = async () => {
    try {
      const students = JSON.parse(batchStudents);
      const res = await api.post("/students/batch", { students });
      setBatchStudents("");
      fetchStudents();
      showMessage(res.data.message);
    } catch (err) {
      if (err instanceof SyntaxError) {
        showMessage("Invalid JSON format", "error");
      } else {
        showMessage(err.response?.data?.error || "Error in batch operation", "error");
      }
    }
  };

  const transferStudents = async () => {
    try {
      const res = await api.post("/students/transfer", {
        from_course_id: parseInt(transfer.from),
        to_course_id: parseInt(transfer.to),
      });
      fetchStudents();
      showMessage(res.data.message);
    } catch (err) {
      showMessage(err.response?.data?.error || "Error transferring students", "error");
    }
  };

  const renderMessage = () => {
    if (!message.text) return null;
    const bgColor = message.type === "error" ? "#e74c3c" : "#27ae60";
    return (
      <div
        style={{
          position: "fixed",
          top: "20px",
          right: "20px",
          padding: "15px 25px",
          backgroundColor: bgColor,
          color: "white",
          borderRadius: "4px",
          zIndex: 1000,
          boxShadow: "0 4px 6px rgba(0,0,0,0.2)",
        }}
      >
        {message.text}
      </div>
    );
  };

  const renderStudentsTab = () => (
    <>
      {/* Add Student Form */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Add New Student</h3>
        <div>
          <input
            style={styles.input}
            placeholder="Name"
            value={newStudent.name}
            onChange={(e) => setNewStudent({ ...newStudent, name: e.target.value })}
          />
          <input
            style={styles.input}
            placeholder="Age"
            type="number"
            value={newStudent.age}
            onChange={(e) => setNewStudent({ ...newStudent, age: e.target.value })}
          />
          <input
            style={styles.input}
            placeholder="GPA (0.0-4.0)"
            type="number"
            step="0.01"
            min="0"
            max="4"
            value={newStudent.gpa}
            onChange={(e) => setNewStudent({ ...newStudent, gpa: e.target.value })}
          />
          <select
            style={styles.select}
            value={newStudent.course_id}
            onChange={(e) => setNewStudent({ ...newStudent, course_id: e.target.value })}
          >
            <option value="">Select Course</option>
            {/* DYNAMICALLY POPULATED FROM DATABASE - Stage 2 Requirement */}
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            style={{ ...styles.button, ...styles.successButton }}
            onClick={addStudent}
          >
            Add Student
          </button>
        </div>
      </div>

      {/* Filter Students */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Filter Students (Report)</h3>
        <p style={{ color: "#7f8c8d", fontSize: "14px", marginBottom: "10px" }}>
          Uses database indexes: idx_students_age, idx_students_gpa, idx_students_course_id
        </p>
        <div>
          <input
            style={styles.input}
            name="ageMin"
            type="number"
            placeholder="Min Age"
            value={filters.ageMin}
            onChange={handleFilterChange}
          />
          <input
            style={styles.input}
            name="ageMax"
            type="number"
            placeholder="Max Age"
            value={filters.ageMax}
            onChange={handleFilterChange}
          />
          <input
            style={styles.input}
            name="gpaMin"
            type="number"
            step="0.01"
            placeholder="Min GPA"
            value={filters.gpaMin}
            onChange={handleFilterChange}
          />
          <input
            style={styles.input}
            name="gpaMax"
            type="number"
            step="0.01"
            placeholder="Max GPA"
            value={filters.gpaMax}
            onChange={handleFilterChange}
          />
          <select
            style={styles.select}
            name="courseId"
            value={filters.courseId}
            onChange={handleFilterChange}
          >
            <option value="">All Courses</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={applyFilter}
          >
            Apply Filter
          </button>
          <button
            style={{ ...styles.button, ...styles.warningButton }}
            onClick={clearFilters}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Students Table */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Students List ({students.length} records)</h3>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Name</th>
              <th style={styles.th}>Age</th>
              <th style={styles.th}>GPA</th>
              <th style={styles.th}>Course</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s, idx) => (
              <tr key={s.id} style={{ backgroundColor: idx % 2 === 0 ? "#f9f9f9" : "white" }}>
                <td style={styles.td}>{s.id}</td>
                <td style={styles.td}>{s.name}</td>
                <td style={styles.td}>{s.age}</td>
                <td style={styles.td}>{s.gpa?.toFixed(2)}</td>
                <td style={styles.td}>{s.course_name || "None"}</td>
                <td style={styles.td}>
                  <button
                    style={{ ...styles.button, ...styles.primaryButton, padding: "5px 10px" }}
                    onClick={() => startEdit(s)}
                  >
                    Edit
                  </button>
                  <button
                    style={{ ...styles.button, ...styles.dangerButton, padding: "5px 10px" }}
                    onClick={() => deleteStudent(s.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Form */}
      {editingStudent && (
        <div style={{ ...styles.section, border: "2px solid #3498db" }}>
          <h3 style={styles.sectionTitle}>Edit Student (ID: {editingStudent.id})</h3>
          <div>
            <input
              style={styles.input}
              value={editingStudent.name}
              onChange={(e) => setEditingStudent({ ...editingStudent, name: e.target.value })}
            />
            <input
              style={styles.input}
              type="number"
              value={editingStudent.age}
              onChange={(e) => setEditingStudent({ ...editingStudent, age: e.target.value })}
            />
            <input
              style={styles.input}
              type="number"
              step="0.01"
              value={editingStudent.gpa}
              onChange={(e) => setEditingStudent({ ...editingStudent, gpa: e.target.value })}
            />
            <select
              style={styles.select}
              value={editingStudent.course_id || ""}
              onChange={(e) => setEditingStudent({ ...editingStudent, course_id: e.target.value })}
            >
              <option value="">Select Course</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <button
              style={{ ...styles.button, ...styles.successButton }}
              onClick={updateStudent}
            >
              Save Changes
            </button>
            <button
              style={{ ...styles.button, ...styles.warningButton }}
              onClick={() => setEditingStudent(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );

  const renderCoursesTab = () => (
    <>
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Add New Course</h3>
        <div>
          <input
            style={{ ...styles.input, width: "300px" }}
            placeholder="Course Name"
            value={newCourse}
            onChange={(e) => setNewCourse(e.target.value)}
          />
          <button
            style={{ ...styles.button, ...styles.successButton }}
            onClick={addCourse}
          >
            Add Course
          </button>
        </div>
      </div>

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Available Courses</h3>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Course Name</th>
            </tr>
          </thead>
          <tbody>
            {courses.map((c, idx) => (
              <tr key={c.id} style={{ backgroundColor: idx % 2 === 0 ? "#f9f9f9" : "white" }}>
                <td style={styles.td}>{c.id}</td>
                <td style={styles.td}>{c.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );

  const renderTransactionsTab = () => (
    <>
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Batch Add Students (Transaction Demo)</h3>
        <p style={{ color: "#7f8c8d", marginBottom: "10px" }}>
          <strong>Stage 3:</strong> All students are added in a single transaction. 
          If any validation fails, ALL inserts are rolled back.
        </p>
        <textarea
          style={{ ...styles.input, width: "100%", height: "150px", fontFamily: "monospace" }}
          placeholder={`Enter students as JSON array, e.g.:
[
  {"name": "John Doe", "age": 20, "gpa": 3.5, "course_id": 1},
  {"name": "Jane Smith", "age": 21, "gpa": 3.8, "course_id": 2}
]`}
          value={batchStudents}
          onChange={(e) => setBatchStudents(e.target.value)}
        />
        <br />
        <button
          style={{ ...styles.button, ...styles.successButton }}
          onClick={batchAddStudents}
        >
          Batch Add (With Transaction)
        </button>
      </div>

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Transfer Students Between Courses</h3>
        <p style={{ color: "#7f8c8d", marginBottom: "10px" }}>
          <strong>Stage 3:</strong> Demonstrates atomic multi-record update within a transaction.
          Uses IMMEDIATE isolation level to prevent concurrent modifications.
        </p>
        <div>
          <select
            style={styles.select}
            value={transfer.from}
            onChange={(e) => setTransfer({ ...transfer, from: e.target.value })}
          >
            <option value="">From Course...</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <span style={{ margin: "0 10px" }}>→</span>
          <select
            style={styles.select}
            value={transfer.to}
            onChange={(e) => setTransfer({ ...transfer, to: e.target.value })}
          >
            <option value="">To Course...</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={transferStudents}
          >
            Transfer All Students
          </button>
        </div>
      </div>

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Transaction Implementation Details</h3>
        <div style={styles.codeBlock}>
{`# ISOLATION LEVEL: IMMEDIATE
# - Acquires RESERVED lock immediately when transaction begins
# - Prevents other writers but allows readers
# - Chosen because:
#   1. Prevents dirty reads (reading uncommitted data)
#   2. Prevents lost updates in concurrent scenarios
#   3. Good balance of consistency vs performance

conn = sqlite3.connect(DB_FILE, timeout=30)
conn.isolation_level = 'IMMEDIATE'

try:
    # Perform multiple operations
    cursor.execute("INSERT INTO students ...", params)
    cursor.execute("INSERT INTO students ...", params)
    
    # All succeeded - commit
    conn.commit()
except:
    # Error - rollback ALL changes
    conn.rollback()
    raise`}
        </div>
      </div>
    </>
  );

  const renderDatabaseTab = () => (
    <>
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Database Schema & Indexes</h3>
        <button
          style={{ ...styles.button, ...styles.primaryButton }}
          onClick={fetchDbInfo}
        >
          Load Database Info
        </button>

        {dbInfo && (
          <>
            <h4 style={{ marginTop: "20px", color: "#2c3e50" }}>Tables</h4>
            {dbInfo.tables.map((t) => (
              <div key={t.name} style={{ marginBottom: "15px" }}>
                <strong>{t.name}</strong>
                <pre style={styles.codeBlock}>{t.sql}</pre>
              </div>
            ))}

            <h4 style={{ marginTop: "20px", color: "#2c3e50" }}>Indexes (Stage 3 Requirement)</h4>
            {dbInfo.indexes.map((idx) => (
              <div key={idx.name} style={{ marginBottom: "15px" }}>
                <span style={{ ...styles.badge, backgroundColor: "#3498db", color: "white" }}>
                  {idx.table}
                </span>
                <strong>{idx.name}</strong>
                <pre style={styles.codeBlock}>{idx.sql}</pre>
              </div>
            ))}
          </>
        )}
      </div>

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Query Execution Plans (Index Usage Demo)</h3>
        <p style={{ color: "#7f8c8d", marginBottom: "10px" }}>
          Click buttons below to see how SQLite uses indexes for different queries:
        </p>
        <div>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => fetchQueryPlan("age_filter")}
          >
            Age Filter Query
          </button>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => fetchQueryPlan("gpa_filter")}
          >
            GPA Filter Query
          </button>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => fetchQueryPlan("course_filter")}
          >
            Course Filter Query
          </button>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => fetchQueryPlan("combined")}
          >
            Combined Filter
          </button>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => fetchQueryPlan("join")}
          >
            JOIN Query
          </button>
        </div>

        {queryPlan && (
          <div style={{ marginTop: "20px" }}>
            <h4>Query Plan: {queryPlan.type}</h4>
            <pre style={styles.codeBlock}>
              {JSON.stringify(queryPlan.data, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>SQL Injection Protection (Stage 3)</h3>
        <div style={styles.codeBlock}>
{`# PROTECTION METHOD 1: Parameterized Queries (Prepared Statements)
# User input is NEVER concatenated into SQL strings

# UNSAFE (vulnerable to SQL injection):
query = f"SELECT * FROM students WHERE name = '{user_input}'"

# SAFE (parameterized query):
query = "SELECT * FROM students WHERE name = ?"
cursor.execute(query, (user_input,))

# PROTECTION METHOD 2: Input Validation & Sanitization
def sanitize_string(value, max_length=100):
    value = str(value).strip()[:max_length]
    value = re.sub(r'[<>";\\\\]', '', value)
    return value

def validate_integer(value, min_val=None, max_val=None):
    int_val = int(value)
    if min_val and int_val < min_val: raise ValueError()
    if max_val and int_val > max_val: raise ValueError()
    return int_val`}
        </div>
      </div>
    </>
  );

  return (
    <div style={styles.container}>
      {renderMessage()}

      <div style={styles.header}>
        <h1 style={{ margin: 0 }}>🎓 Student Management System</h1>
        <p style={{ margin: "10px 0 0 0", opacity: 0.9 }}>
          CS348 Stage 3 - SQL Injection Protection, Indexes, and Transactions
        </p>
      </div>

      <div style={styles.tabs}>
        {["students", "courses", "transactions", "database"].map((tab) => (
          <button
            key={tab}
            style={{
              ...styles.tab,
              ...(activeTab === tab ? styles.activeTab : {}),
            }}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === "students" && renderStudentsTab()}
      {activeTab === "courses" && renderCoursesTab()}
      {activeTab === "transactions" && renderTransactionsTab()}
      {activeTab === "database" && renderDatabaseTab()}

      <div style={{ ...styles.section, backgroundColor: "#2c3e50", color: "white" }}>
        <h3 style={{ color: "white", borderColor: "#3498db" }}>Stage 3 Implementation Summary</h3>
        <ul>
          <li><strong>SQL Injection Protection:</strong> All queries use parameterized statements (?). Input validation via sanitize_string(), validate_integer(), validate_float().</li>
          <li><strong>Database Indexes:</strong> idx_students_age, idx_students_gpa, idx_students_course_id, idx_students_age_gpa (composite). See Database tab for details.</li>
          <li><strong>Transactions:</strong> IMMEDIATE isolation level for write operations. Batch operations with automatic rollback on failure. See Transactions tab for demo.</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
