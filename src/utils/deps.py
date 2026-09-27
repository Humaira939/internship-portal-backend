from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.utils.db import get_db
from src.utils.settings import settings
from src.student.model import StudentModel
from src.company.model import CompanyModel

# This tells FastAPI to expect a token in the "Authorization: Bearer <token>" header
bearer_scheme = HTTPBearer()

ALGORITHM = "HS256"


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Try to decode the token; if it's invalid or expired, this will fail
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find the student that this token belongs to
    student = db.query(StudentModel).filter(StudentModel.email == email).first()
    if not student:
        raise HTTPException(status_code=401, detail="Student not found")

    return student


def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    company = db.query(CompanyModel).filter(CompanyModel.email == email).first()
    if not company:
        raise HTTPException(status_code=401, detail="Company not found")

    return company