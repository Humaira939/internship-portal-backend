from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from src.student.controller import login_student, register_student
from src.student.dto import StudentLoginRequest, StudentSignupRequest, TokenResponse
from src.utils.db import get_db
from src.utils.security import create_access_token

router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(
    name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    phone: str = Form(""),
    university: str = Form(""),
    degree: str = Form(""),
    graduation_status: str = Form(""),
    semester: str = Form(""),
    graduation_year: str = Form(""),
    graduation_date: str = Form(""),
    skills: str = Form(""),
    location: str = Form(""),
    linkedin: str = Form(""),
    github: str = Form(""),
    portfolio: str = Form(""),
    resume: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    data = StudentSignupRequest(
        name=name, email=email, password=password, phone=phone,
        university=university, degree=degree,
        graduation_status=graduation_status, semester=semester,
        graduation_year=graduation_year, graduation_date=graduation_date,
        skills=skills, location=location,
        linkedin=linkedin, github=github, portfolio=portfolio,
    )
    student = register_student(data, resume, db)
    token = create_access_token({"sub": student.email, "role": "student"})
    return TokenResponse(access_token=token, student=student)


@router.post("/login", response_model=TokenResponse)
def login(data: StudentLoginRequest, db: Session = Depends(get_db)):
    student = login_student(data, db)
    token = create_access_token({"sub": student.email, "role": "student"})
    return TokenResponse(access_token=token, student=student)