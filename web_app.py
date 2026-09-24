"""Small browser UI for the student registry."""
from flask import Flask, jsonify, request
from student_management import Grade, Registry, Student, seed, student_report

app = Flask(__name__)
registry = Registry()
seed(registry)

@app.get("/")
def home():
    return """<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Student Management</title><style>
    body{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 18px;background:#f4f7fb;color:#172033}
    .card{background:white;padding:22px;border-radius:16px;margin:16px 0;box-shadow:0 8px 24px #17203318}
    input,button{padding:10px;border:1px solid #ccd5e5;border-radius:8px;margin:4px}button{background:#5865f2;color:white;border:0;cursor:pointer}
    table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #e5e9f2}
    </style><h1>Student Management System</h1><div class=card><h2>Students</h2><table id=students></table></div>
    <div class=card><h2>Add student</h2><form id=form><input name=id placeholder="ID" required><input name=first placeholder="First name" required>
    <input name=last placeholder="Last name" required><input name=email placeholder="Email" required><button>Add</button></form></div>
    <div class=card><h2>Student report</h2><input id=reportId placeholder="Student ID"><button onclick=report()>Show report</button><pre id=output></pre></div>
    <script>
    async function load(){let r=await fetch('/api/students');let d=await r.json();students.innerHTML='<tr><th>ID</th><th>Name</th><th>Email</th><th>Average</th></tr>'+d.map(s=>`<tr><td>${s.id}</td><td>${s.name}</td><td>${s.email}</td><td>${s.average}</td></tr>`).join('')}
    form.onsubmit=async e=>{e.preventDefault();let x=Object.fromEntries(new FormData(form));let r=await fetch('/api/students',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(x)});if(!r.ok)alert((await r.json()).error);else{form.reset();load()}}
    async function report(){let r=await fetch('/api/students/'+reportId.value+'/report');output.textContent=r.ok?await r.text():(await r.json()).error} load()
    </script>"""

@app.get("/api/students")
def students():
    return jsonify([{"id": s.student_id, "name": s.full_name, "email": s.email,
                     "average": round(s.average, 1) if s.average is not None else None} for s in registry.all()])

@app.post("/api/students")
def add_student():
    data = request.get_json() or {}
    try:
        registry.add(Student(data["id"], data["first"], data["last"], data["email"]))
    except (KeyError, ValueError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(ok=True), 201

@app.get("/api/students/<student_id>/report")
def report(student_id):
    try:
        return student_report(registry.require(student_id)), 200, {"Content-Type": "text/plain"}
    except ValueError as error:
        return jsonify(error=str(error)), 404

if __name__ == "__main__":
    app.run(debug=True)
