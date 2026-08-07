from sqlalchemy.orm import Session
from .models import Teacher, Student, Course, Enrollment

def seed(session: Session) -> None:
    if session.query(Teacher).first():
        return  # already seeded
    t1 = Teacher(first_name="Alice", last_name="Smith", city="Portland", active=True)
    t2 = Teacher(first_name="Marco", last_name="Johnson", city="Eugene", active=True)
    s1 = Student(first_name="Linh", last_name="Nguyen", city="Bend", birthdate="20040105", gpa=3.33, active=True)
    s2 = Student(first_name="Diana", last_name="Brown", city="Corvallis", birthdate="20030530", gpa=3.12, active=False)
    s3 = Student(first_name="Eve", last_name="Garcia", city="Ashland", birthdate="20021119", gpa=4.0, active=True)
    c1 = Course(code="CS101", title="Intro to CS", credits=3, teacher=t1)
    c2 = Course(code="MATH201", title="Discrete Math", credits=4, teacher=t2)
    e1 = Enrollment(student=s1, course=c1, grade="A")
    e2 = Enrollment(student=s2, course=c2, grade="B")
    e3 = Enrollment(student=s3, course=c1, grade="A")
    session.add_all([t1, t2, s1, s2, s3, c1, c2, e1, e2, e3])
    session.commit()
