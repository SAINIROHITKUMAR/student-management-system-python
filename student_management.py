"""Dependency-free student records, grades, CSV persistence, and reports."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Grade:
    subject: str
    score: float

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("Subject is required.")
        if not 0 <= self.score <= 100:
            raise ValueError("Score must be between 0 and 100.")

    @property
    def letter(self) -> str:
        return "A" if self.score >= 90 else "B" if self.score >= 80 else "C" if self.score >= 70 else "D" if self.score >= 60 else "F"


@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str
    grades: dict[str, Grade] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, label in ((self.student_id, "Student ID"), (self.first_name, "First name"),
                             (self.last_name, "Last name"), (self.email, "Email")):
            if not value.strip():
                raise ValueError(f"{label} is required.")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def average(self) -> float | None:
        return sum(g.score for g in self.grades.values()) / len(self.grades) if self.grades else None

    @property
    def passed(self) -> bool:
        return self.average is not None and self.average >= 60

    def add_grade(self, grade: Grade) -> None:
        self.grades[grade.subject] = grade


class Registry:
    HEADER = ["studentId", "firstName", "lastName", "email", "subject", "score"]

    def __init__(self) -> None:
        self.students: dict[str, Student] = {}

    def add(self, student: Student) -> None:
        if student.student_id in self.students:
            raise ValueError(f"A student with ID {student.student_id} already exists.")
        self.students[student.student_id] = student

    def require(self, student_id: str) -> Student:
        if student_id not in self.students:
            raise ValueError(f"Student not found: {student_id}")
        return self.students[student_id]

    def search(self, query: str) -> list[Student]:
        query = query.lower()
        return [s for s in self.all() if query in f"{s.student_id} {s.full_name} {s.email}".lower()]

    def all(self) -> list[Student]:
        return sorted(self.students.values(), key=lambda s: s.student_id)

    def save(self, path: str | Path) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(self.HEADER)
            for student in self.all():
                grades = student.grades.values() or [None]
                for grade in grades:
                    writer.writerow([student.student_id, student.first_name, student.last_name, student.email,
                                      grade.subject if grade else "", grade.score if grade else ""])

    def load(self, path: str | Path) -> int:
        loaded: dict[str, Student] = {}
        with Path(path).open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                student = loaded.setdefault(row["studentId"], Student(row["studentId"], row["firstName"],
                                                                        row["lastName"], row["email"]))
                if row["subject"]:
                    student.add_grade(Grade(row["subject"], float(row["score"])))
        self.students = loaded
        return len(loaded)


def student_report(student: Student) -> str:
    lines = ["\nStudent Report", "--------------", f"{student.student_id} | {student.full_name} | {student.email}"]
    if not student.grades:
        return "\n".join(lines + ["No grades recorded.", "Average: N/A", "Status: N/A"])
    lines += ["Grades:"] + [f"  - {g.subject}: {g.score:.1f} ({g.letter})" for g in student.grades.values()]
    lines += [f"Average: {student.average:.1f}", f"Status: {'PASS' if student.passed else 'AT RISK'}"]
    return "\n".join(lines)


def class_report(students: list[Student]) -> str:
    graded = [s for s in students if s.average is not None]
    average = sum(s.average for s in graded) / len(graded) if graded else None
    passed = sum(s.passed for s in graded)
    rate = f"{passed * 100 / len(graded):.1f}%" if graded else "N/A"
    return (f"\nClass Report\n------------\nStudents: {len(students)}\n"
            f"Students with grades: {len(graded)}\nClass average: {average:.1f}\nPass rate: {rate}\n"
            if average is not None else f"\nClass Report\n------------\nStudents: {len(students)}\nStudents with grades: 0\nClass average: N/A\nPass rate: N/A\n")


def seed(registry: Registry) -> None:
    ada = Student("S001", "Ada", "Lovelace", "ada@example.com")
    ada.add_grade(Grade("Mathematics", 96)); ada.add_grade(Grade("Physics", 91))
    alan = Student("S002", "Alan", "Turing", "alan@example.com")
    alan.add_grade(Grade("Mathematics", 84)); alan.add_grade(Grade("Computer Science", 94))
    registry.add(ada); registry.add(alan)


def main() -> None:
    registry = Registry(); seed(registry)
    actions = {"1": lambda: print("\n".join(f"{s.student_id:<8} {s.full_name:<24} {s.email:<28} {s.average if s.average is not None else 'N/A'}" for s in registry.all())),
               "4": lambda: print(student_report(registry.require(input("Student ID: ").strip()))),
               "5": lambda: print("\n".join(f"{s.student_id} | {s.full_name} | {s.email}" for s in registry.search(input("Search: ")))),
               "6": lambda: print("Removed." if registry.students.pop(input("Student ID: ").strip(), None) else "Student not found.")}
    print("Student Management System (Python)")
    while True:
        print("\n[1] List [2] Add student [3] Record grade [4] Report [5] Search [6] Remove [7] Save CSV [8] Load CSV [0] Exit")
        choice = input("> ").strip()
        try:
            if choice == "0": print("Goodbye."); return
            if choice in actions: actions[choice]()
            elif choice == "2":
                student = Student(input("ID: "), input("First name: "), input("Last name: "), input("Email: "))
                registry.add(student); print("Student added.")
            elif choice == "3":
                registry.require(input("Student ID: ")).add_grade(Grade(input("Subject: "), float(input("Score (0-100): "))))
                print("Grade recorded.")
            elif choice == "7": registry.save(input("CSV path: ")); print("Saved.")
            elif choice == "8": print(f"Loaded {registry.load(input('CSV path: '))} student(s).")
            else: print("Please choose a number from 0 to 8.")
        except (ValueError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
