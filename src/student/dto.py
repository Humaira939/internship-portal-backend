from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============ REQUEST: registration form (every value arrives as text) ============
class StudentSignupRequest(BaseModel):
    name: str = ""
    email: str = ""
    password: str = ""
    phone: str = ""
    university: str = ""
    degree: str = ""
    graduation_status: str = ""  # "yes" (graduated) or "no" (still studying)
    semester: str = ""
    graduation_year: str = ""
    graduation_date: str = ""    # format YYYY-MM-DD
    skills: str = ""             # comma separated, e.g. "Python, React"
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


# ============ REQUEST: login ============
class StudentLoginRequest(BaseModel):
    email: str
    password: str


# ============ REQUEST: forgot password ============
class ForgotPasswordRequest(BaseModel):
    email: str


# ============ RESPONSES (password_hash is never included) ============
class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: Optional[str] = None
    university: Optional[str] = None
    degree: Optional[str] = None
    graduation_status: Optional[str] = None
    semester: Optional[str] = None
    graduation_year: Optional[str] = None
    graduation_date: Optional[datetime] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentResponse