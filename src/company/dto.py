from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============ REQUEST: company registration form (every value arrives as text) ============
class CompanySignupRequest(BaseModel):
    company_name: str = ""
    email: str = ""
    password: str = ""
    industry: str = ""
    contact_person: str = ""
    phone: str = ""
    location: str = ""
    website: str = ""            # optional
    description: str = ""        # optional
    license_issue_date: str = ""   # format YYYY-MM-DD
    license_expiry_date: str = ""  # format YYYY-MM-DD


# ============ REQUEST: login ============
class CompanyLoginRequest(BaseModel):
    email: str
    password: str


# ============ RESPONSES (password_hash and file path are never included) ============
class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    email: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    license_issue_date: Optional[date] = None
    license_expiry_date: Optional[date] = None
    created_at: datetime


class CompanyTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    company: CompanyResponse