# models.py

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between Student and Course
student_course_table = Table(
    'student_course',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    students = relationship('Student', secondary=student_course_table, back_populates='enrolled_courses')
    notes = relationship('Note', back_populates='course')

    def __repr__(self):
        return f"<Course(title={self.title})>"

class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    enrolled_courses = relationship('Course', secondary=student_course_table, back_populates='students')

    def __repr__(self):
        return f"<Student(username={self.username})>"

class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    created_by = Column(String(150), nullable=True)  # can be username or email
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship('Course', back_populates='notes')

    def __repr__(self):
        return f"<Note(title={self.title}, course={self.course.title})>"
