from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.utils.db import get_db
from src.student.dto import StudentSignupRequest, StudentLoginRequest, StudentResponse, TokenResponse
from src.student.controller import register_student, login_student
from src.utils.security import create_access_token

router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/signup", response_model=StudentResponse)
def signup(data: StudentSignupRequest, db: Session = Depends(get_db)):
    return register_student(data, db)


@router.post("/login", response_model=TokenResponse)
def login(data: StudentLoginRequest, db: Session = Depends(get_db)):
    student = login_student(data, db)
    token = create_access_token({"sub": student.email})
    return TokenResponse(access_token=token, student=student)