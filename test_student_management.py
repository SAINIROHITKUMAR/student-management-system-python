import tempfile
import unittest
from pathlib import Path

from student_management import Grade, Registry, Student, student_report


class StudentManagementTests(unittest.TestCase):
    def test_grade_validation_and_letter(self):
        self.assertEqual(Grade("Math", 90).letter, "A")
        with self.assertRaises(ValueError):
            Grade("Math", 101)

    def test_average_replaces_subject(self):
        student = Student("S1", "Test", "Student", "test@example.com")
        student.add_grade(Grade("Math", 80))
        student.add_grade(Grade("Science", 100))
        student.add_grade(Grade("Math", 60))
        self.assertEqual(student.average, 80)

    def test_csv_round_trip_and_search(self):
        registry = Registry()
        student = Student("S1", "Grace", "Hopper", "grace@example.com")
        student.add_grade(Grade("Programming", 99))
        registry.add(student)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "students.csv"
            registry.save(path)
            restored = Registry()
            self.assertEqual(restored.load(path), 1)
            self.assertEqual(restored.require("S1").average, 99)
        self.assertEqual(len(registry.search("hopper")), 1)

    def test_report(self):
        student = Student("S1", "Test", "Student", "test@example.com")
        student.add_grade(Grade("Math", 75))
        self.assertIn("Average: 75.0", student_report(student))


if __name__ == "__main__":
    unittest.main()
