from fastapi import HTTPException,status
from pwdlib import PasswordHash
from sqlalchemy.orm import session
from src.student.dto import StudentCreateDTO
from src.student.model import StudentModel

# Setup Argon2 password hasher using pwdlib
password_hash = PasswordHash.recommended()

def create_student(body: StudentCreateDTO,db: session):
    """Register a new student account in the portal."""

    #Check if a student with the given email already exists
    existing_student = (
    db.query(StudentModel).filter(StudentModel.email == body.email).first() 
    )
    if existing_student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="user with this email already exist")
    
    # Step 2: Hash the plain text password securely using Argon2
    hashed_password =password_hash.hash(body.password)

    # Step 3: Create student record with default values for AI module compatibility
    new_student = StudentModel(
        name = body.name,
        email = body.email,
        password_hash = hashed_password,
        skills = [],         # Ensures empty array in DB for skill-overlap calculations
        resume_path = None,  # Placeholder for future resume upload feature
    )

    # Step 4: Save record permanently into PostgreSQL database
    db.add(new_student),
    db.commit(),
    db.refresh(new_student)

    # Step 5: Return newly created student object
    return new_student