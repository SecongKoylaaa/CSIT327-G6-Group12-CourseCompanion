from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from myapp.models import Base, Course, Student, Note

# Replace with your actual Supabase URI
DATABASE_URL = "postgresql://postgres.tkyztssepvewbmgsaaeq:282004@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

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
