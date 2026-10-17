from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
 
from src.admin.model import AdminModel
from src.company.controller import ensure_company_can_post
from src.company.model import CompanyModel, CompanyStatus
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
 
    # Special-purpose tokens (for example the password reset link token) are NOT login tokens.
    # Without this check, a reset token (same secret key, has "sub" and "role") would work as a login token.
    if payload.get("purpose") is not None:
        raise HTTPException(status_code=401, detail="Invalid token")
 
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
 
    # A valid token of ANOTHER role (e.g. a student token on a company route) is refused
    if payload.get("role") != expected_role:
        raise HTTPException(status_code=403, detail="Access denied for this role")
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
 
    # A company blocked AFTER it logged in must lose access immediately (its old token still works otherwise)
    if company.verification_status == CompanyStatus.BLOCKED:
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Please contact the administrator.",
        )
    return company
 
 
def get_verified_company(company: CompanyModel = Depends(get_current_company)):
    # Use this on every route that needs a verified company (for example: posting an internship).
    # It raises 403 with a clear message if the company is pending / rejected / blocked / license expired.
    return ensure_company_can_post(company)
 
 
def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    email = _read_token(credentials, "admin")
    admin = db.query(AdminModel).filter(AdminModel.email == email).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin