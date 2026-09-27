from sqlalchemy.orm import Session
from fastapi import HTTPException
from pwdlib import PasswordHash

from src.student.model import StudentModel
from src.student.dto import StudentSignupRequest, StudentLoginRequest

# Used to securely hash and verify passwords
password_hash = PasswordHash.recommended()


def register_student(data: StudentSignupRequest, db: Session):
    # Check if email is already registered
    existing_student = db.query(StudentModel).filter(StudentModel.email == data.email).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before saving (never save plain text password)
    hashed_password = password_hash.hash(data.password)

    # Create new student record
    new_student = StudentModel(
        name=data.name,
        email=data.email,
        password_hash=hashed_password
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


def login_student(data: StudentLoginRequest, db: Session):
    # Find student by email
    student = db.query(StudentModel).filter(StudentModel.email == data.email).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password against stored hash
    if not password_hash.verify(data.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return student