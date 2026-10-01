import re
from datetime import date, datetime

from fastapi import HTTPException, UploadFile
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.student.dto import StudentLoginRequest, StudentSignupRequest
from src.student.model import StudentModel
from src.utils.email_sender import send_reset_email
from src.utils.password_reset import create_reset_token
from src.utils.settings import settings
from src.utils.supabase_storage import delete_file, upload_resume

# Used to securely hash and verify passwords
password_hash = PasswordHash.recommended()

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\+?[0-9\s\-]{7,20}$"


def bad_request(message: str) -> HTTPException:
    # Every validation problem is returned as {"detail": "message"}
    return HTTPException(status_code=400, detail=message)


def register_student(data: StudentSignupRequest, resume: UploadFile, db: Session):
    # ---------- 1. Clean the values (remove extra spaces) ----------
    name = data.name.strip()
    email = data.email.strip().lower()
    phone = data.phone.strip()
    university = data.university.strip()
    degree = data.degree.strip()
    status = data.graduation_status.strip().lower()
    semester = data.semester.strip()
    graduation_year = data.graduation_year.strip()
    graduation_date_text = data.graduation_date.strip()
    location = data.location.strip()
    linkedin = data.linkedin.strip()
    github = data.github.strip()
    portfolio = data.portfolio.strip()

    # ---------- 2. Check the rules ----------
    if len(name) < 2:
        raise bad_request("Please enter your full name.")
    if not re.match(EMAIL_PATTERN, email):
        raise bad_request("Please enter a valid email address.")
    if len(data.password) < 6:
        raise bad_request("Password must be at least 6 characters long.")
    if not re.match(PHONE_PATTERN, phone):
        raise bad_request("Please enter a valid phone number.")
    if not university:
        raise bad_request("Please enter your university.")
    if not degree:
        raise bad_request("Please select your degree.")
    if status not in ("yes", "no"):
        raise bad_request("Please select your graduation status.")

    graduation_date = None
    if status == "no":
        # Still studying: the current semester is needed
        if not semester:
            raise bad_request("Please select your current semester.")
        graduation_year = ""
    else:
        # Graduated: graduation year and date are needed
        if not graduation_year:
            raise bad_request("Please select your graduation year.")
        if not graduation_date_text:
            raise bad_request("Please select your graduation date.")
        try:
            graduation_date = datetime.strptime(graduation_date_text, "%Y-%m-%d")
        except ValueError:
            raise bad_request("Graduation date is not valid.")
        if graduation_date.date() > date.today():
            raise bad_request("Graduation date cannot be in the future.")
        semester = ""

    for link in (linkedin, github, portfolio):
        if link and not link.lower().startswith(("http://", "https://")):
            raise bad_request("Links must start with http:// or https://")

    # The resume is mandatory
    if resume is None or not getattr(resume, "filename", None):
        raise bad_request("Please upload your resume (PDF).")

    # "Python, React, python" -> ["Python", "React"]
    skills = []
    for item in data.skills.split(","):
        skill = item.strip()
        if skill and skill.lower() not in [s.lower() for s in skills]:
            skills.append(skill)

    # ---------- 3. Email must be new (checked BEFORE uploading the file) ----------
    if db.query(StudentModel).filter(StudentModel.email == email).first():
        raise bad_request("Email already registered.")

    # ---------- 4. Upload the resume, then save the student ----------
    resume_path = upload_resume(resume)

    student = StudentModel(
        name=name,
        email=email,
        password_hash=password_hash.hash(data.password),
        phone=phone,
        university=university,
        degree=degree,
        graduation_status=status,
        semester=semester or None,
        graduation_year=graduation_year or None,
        graduation_date=graduation_date,
        skills=skills or None,
        location=location or None,
        linkedin=linkedin or None,
        github=github or None,
        portfolio=portfolio or None,
        resume_path=resume_path,
    )

    try:
        db.add(student)
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        delete_file(settings.RESUME_BUCKET, resume_path)
        raise bad_request("Email already registered.")
    except Exception as error:
        db.rollback()
        delete_file(settings.RESUME_BUCKET, resume_path)  # remove the uploaded file again
        print(f"Student signup error: {error}")
        raise HTTPException(status_code=500, detail="Could not create the account. Please try again.")

    return student


def login_student(data: StudentLoginRequest, db: Session):
    email = data.email.strip().lower()
    student = db.query(StudentModel).filter(StudentModel.email == email).first()

    # Same message for both cases, so nobody can find out which emails exist
    if not student or not password_hash.verify(data.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return student


def request_student_password_reset(email: str, db: Session):
    email = email.strip().lower()
    student = db.query(StudentModel).filter(StudentModel.email == email).first()

    if student:
        token = create_reset_token(student.email, "student")
        reset_link = f"{settings.FRONTEND_RESET_URL}?token={token}"
        try:
            send_reset_email(student.email, reset_link)
        except Exception as error:
            print(f"Could not send reset email: {error}")  # testing ke waqt error yahan dikhega

    # Same message chahe email registered ho ya na ho — taake koi pata na laga sake
    # ke kaunsi emails system mein registered hain
    return {"message": "If this email is registered, a password reset link has been sent."}