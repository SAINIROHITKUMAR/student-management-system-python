# Student Management System (Python)

A standard-library-only Python 3.10+ CLI for student records, subject grades, CSV persistence, and individual/class reports.

## Run

```powershell
python student_management.py
```

## Test

```powershell
python -m unittest -v
```

The app seeds sample records on startup. Menu options cover listing, adding students, recording grades, searching, removing, reporting, and CSV save/load. CSV columns are `studentId,firstName,lastName,email,subject,score`.
