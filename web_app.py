"""Small browser UI for the student registry."""
from flask import Flask, jsonify, request
from student_management import Grade, Registry, Student, seed, student_report

app = Flask(__name__)
registry = Registry()
seed(registry)


@app.get("/")
def home():
    return """<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Student Management</title>
    <style>
      body { font: 16px system-ui; max-width: 980px; margin: 40px auto; padding: 0 18px; background: #f4f7fb; color: #172033; }
      .card { background: white; padding: 22px; border-radius: 16px; margin: 16px 0; box-shadow: 0 8px 24px rgba(23,32,51,.08); }
      h1 { text-align: center; margin-bottom: 20px; }
      h2 { margin-top: 0; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; }
      input, select, button { padding: 10px; border: 1px solid #ccd5e5; border-radius: 8px; margin: 6px 0; width: 100%; box-sizing: border-box; }
      button { background: #5865f2; color: white; border: 0; cursor: pointer; font-weight: 700; }
      button.secondary { background: #e9ecff; color: #2d3a8c; }
      button.danger { background: #d94d5b; }
      .row { display: flex; gap: 10px; flex-wrap: wrap; }
      .row > * { flex: 1 1 200px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e5e9f2; }
      pre { white-space: pre-wrap; margin: 0; min-height: 120px; background: #f8f9fd; border-radius: 10px; padding: 12px; }
    </style>
    <h1>Student Management System</h1>
    <div class="card">
      <h2>Students</h2>
      <table id="students"></table>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Add student</h2>
        <form id="addStudentForm">
          <div class="row"><input name="id" placeholder="Student ID" required></div>
          <div class="row"><input name="first" placeholder="First name" required><input name="last" placeholder="Last name" required></div>
          <div class="row"><input name="email" type="email" placeholder="Email" required></div>
          <button>Add student</button>
        </form>
      </div>

      <div class="card">
        <h2>Record grade</h2>
        <form id="gradeForm">
          <div class="row"><input name="studentId" id="gradeStudentId" placeholder="Student ID" required></div>
          <div class="row"><input name="subject" placeholder="Subject" required><input name="score" type="number" min="0" max="100" step="0.1" placeholder="Score" required></div>
          <button>Add grade</button>
        </form>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Search students</h2>
        <form id="searchForm">
          <input name="query" placeholder="Search ID or name" required>
          <button class="secondary" type="submit">Search</button>
        </form>
      </div>

      <div class="card">
        <h2>Remove student</h2>
        <form id="removeForm">
          <input name="studentId" placeholder="Student ID" required>
          <button class="danger" type="submit">Remove</button>
        </form>
      </div>
    </div>

    <div class="card">
      <h2>Student report</h2>
      <div class="row"><input id="reportStudentId" placeholder="Student ID"><button class="secondary" onclick="showReport()">Show report</button></div>
      <pre id="reportOutput"></pre>
    </div>

    <script>
      async function loadStudents(search = '') {
        const params = search ? '?search=' + encodeURIComponent(search) : '';
        const res = await fetch('/api/students' + params);
        const students = await res.json();
        const rows = ['<tr><th>ID</th><th>Name</th><th>Email</th><th>Average</th></tr>']
          .concat(students.map(s => `<tr><td>${s.id}</td><td>${s.name}</td><td>${s.email}</td><td>${s.average ?? 'N/A'}</td></tr>`));
        document.getElementById('students').innerHTML = rows.join('');
      }

      document.getElementById('addStudentForm').onsubmit = async (e) => {
        e.preventDefault();
        const payload = Object.fromEntries(new FormData(e.target));
        const res = await fetch('/api/students', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) { alert(data.error || 'Invalid input'); return; }
        e.target.reset();
        loadStudents();
      };

      document.getElementById('gradeForm').onsubmit = async (e) => {
        e.preventDefault();
        const payload = Object.fromEntries(new FormData(e.target));
        const res = await fetch('/api/students/' + encodeURIComponent(payload.studentId) + '/grades', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ subject: payload.subject, score: Number(payload.score) })
        });
        const data = await res.json();
        if (!res.ok) { alert(data.error || 'Could not add grade'); return; }
        e.target.reset();
        loadStudents();
      };

      document.getElementById('searchForm').onsubmit = async (e) => {
        e.preventDefault();
        const query = new FormData(e.target).get('query').toString();
        loadStudents(query);
      };

      document.getElementById('removeForm').onsubmit = async (e) => {
        e.preventDefault();
        const studentId = new FormData(e.target).get('studentId').toString();
        const res = await fetch('/api/students/' + encodeURIComponent(studentId), { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) { alert(data.error || 'Could not remove student'); return; }
        e.target.reset();
        loadStudents();
      };

      window.showReport = async function() {
        const id = document.getElementById('reportStudentId').value;
        const res = await fetch('/api/students/' + encodeURIComponent(id) + '/report');
        const txt = await res.text();
        document.getElementById('reportOutput').textContent = txt || 'Student not found';
      };

      loadStudents();
    </script>
    """


@app.get("/api/students")
def students():
    query = request.args.get("search", "").strip()
    items = registry.search(query) if query else registry.all()
    return jsonify([
        {"id": s.student_id, "name": s.full_name, "email": s.email,
         "average": round(s.average, 1) if s.average is not None else None}
        for s in items
    ])


@app.post("/api/students")
def add_student():
    data = request.get_json() or {}
    try:
        registry.add(Student(data["id"], data["first"], data["last"], data["email"]))
    except (KeyError, ValueError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(ok=True), 201


@app.post("/api/students/<student_id>/grades")
def add_grade(student_id):
    data = request.get_json() or {}
    try:
        subject = data["subject"]
        score = float(data["score"])
        registry.require(student_id).add_grade(Grade(subject, score))
    except (KeyError, TypeError, ValueError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(ok=True), 201


@app.delete("/api/students/<student_id>")
def delete_student(student_id):
    try:
        registry.require(student_id)
    except ValueError as error:
        return jsonify(error=str(error)), 404
    del registry.students[student_id]
    return jsonify(ok=True), 200


@app.get("/api/students/<student_id>/report")
def report(student_id):
    try:
        return student_report(registry.require(student_id)), 200, {"Content-Type": "text/plain; charset=utf-8"}
    except ValueError as error:
        return jsonify(error=str(error)), 404


if __name__ == "__main__":
    app.run(debug=True)
