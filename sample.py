from datetime import datetime
from typing import List


class Person:
    """Base class representing a generic person."""
    
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def contact_info(self) -> str:
        return f"{self.name} <{self.email}>"


class Student(Person):
    """Represents a student enrolled in courses."""

    def __init__(self, name: str, email: str, student_id: str):
        super().__init__(name, email)
        self.student_id = student_id
        self.enrolled_courses: List['Course'] = []

    def enroll(self, course: 'Course'):
        if course not in self.enrolled_courses:
            self.enrolled_courses.append(course)
            course.add_student(self)


class Instructor(Person):
    """Represents an instructor who teaches courses."""

    def __init__(self, name: str, email: str, expertise: str):
        super().__init__(name, email)
        self.expertise = expertise
        self.courses: List['Course'] = []

    def assign_course(self, course: 'Course'):
        if course not in self.courses:
            self.courses.append(course)
            course.instructor = self


# 🔧 MODIFIED CLASS (Added new attribute: description)
class Course:
    """Represents a course with students and an instructor."""

    def __init__(self, course_code: str, title: str):
        self.course_code = course_code
        self.title = title
        self.description = "Default course description"   # ← Added
        self.instructor: Instructor | None = None
        self.students: List[Student] = []
        self.assignments: List['Assignment'] = []

    def add_student(self, student: Student):
        if student not in self.students:
            self.students.append(student)

    def add_assignment(self, assignment: 'Assignment'):
        self.assignments.append(assignment)

    def info(self) -> str:
        instructor_name = self.instructor.name if self.instructor else "Not assigned"
        return f"{self.course_code} - {self.title} (Instructor: {instructor_name})"


class Assignment:
    """Represents an assignment given in a course."""

    def __init__(self, title: str, due_date: datetime):
        self.title = title
        self.due_date = due_date
        self.submissions = []  # Submission class removed, list kept for compatibility


# ✅ NEW CLASS ADDED
class Grade:
    """Represents a grading entry for a student's assignment."""
    
    def __init__(self, student: Student, assignment: Assignment, score: float):
        self.student = student
        self.assignment = assignment
        self.score = score
        self.graded_at = datetime.now()

    def summary(self):
        return f"{self.student.name} scored {self.score} on '{self.assignment.title}'."


# ❌ REMOVED CLASS: Submission
# class Submission:
#     ...


# ---------------------------------------------------------
# Example Usage (for testing your doc generator)
# ---------------------------------------------------------

if __name__ == "__main__":
    instructor = Instructor("Alice Smith", "alice@example.com", "Data Science")
    student1 = Student("Bob Lee", "bob@example.com", "S101")

    course = Course("CS101", "Intro to Python")
    instructor.assign_course(course)
    student1.enroll(course)

    assignment = Assignment("Project 1", datetime(2025, 1, 20))
    course.add_assignment(assignment)

    grade = Grade(student1, assignment, 95)
    print(course.info())
    print(grade.summary())
