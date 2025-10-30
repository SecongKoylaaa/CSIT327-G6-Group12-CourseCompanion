from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Course, Student, Note

# Replace with your actual Supabase URI
DATABASE_URL = "postgresql://postgres:282004@db.tkyztssepvewbmgsaaeq.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL)

# Create tables in Supabase if they don't exist
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Example usage: Add a course
new_course = Course(title="Math 101", description="Basic Math course")
session.add(new_course)
session.commit()

print("Course added:", new_course)
