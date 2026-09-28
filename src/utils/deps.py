from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.company.model import CompanyModel
from src.student.model import StudentModel
from src.utils.db import get_db
from src.utils.settings import settings

# Expects the header:  Authorization: Bearer <token>
bearer_scheme = HTTPBearer()

ALGORITHM = "HS256"


def _read_token(credentials: HTTPAuthorizationCredentials, expected_role: str) -> str:
    # Returns the email stored inside the token, or raises 401
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = payload.get("sub")
    if email is None or payload.get("role") != expected_role:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    email = _read_token(credentials, "student")
    student = db.query(StudentModel).filter(StudentModel.email == email).first()
    if not student:
        raise HTTPException(status_code=401, detail="Student not found")
    return student


def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    email = _read_token(credentials, "company")
    company = db.query(CompanyModel).filter(CompanyModel.email == email).first()
    if not company:
        raise HTTPException(status_code=401, detail="Company not found")
    return company