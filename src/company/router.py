from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from src.company.controller import (
    login_company,
    register_company,
    request_company_password_reset,
    reupload_trade_license,
)
from src.company.dto import (
    CompanyLoginRequest,
    CompanyResponse,
    CompanySignupRequest,
    CompanyTokenResponse,
    ForgotPasswordRequest,
)
from src.company.model import CompanyModel
from src.utils.db import get_db
from src.utils.deps import get_current_company
from src.utils.security import create_access_token

router = APIRouter(prefix="/company", tags=["Company"])


@router.post("/signup", response_model=CompanyTokenResponse, status_code=201)
def signup(
    company_name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    industry: str = Form(""),
    contact_person: str = Form(""),
    phone: str = Form(""),
    location: str = Form(""),
    website: str = Form(""),
    description: str = Form(""),
    license_issue_date: str = Form(""),
    license_expiry_date: str = Form(""),
    trade_license: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    data = CompanySignupRequest(
        company_name=company_name, email=email, password=password,
        industry=industry, contact_person=contact_person, phone=phone,
        location=location, website=website, description=description,
        license_issue_date=license_issue_date,
        license_expiry_date=license_expiry_date,
    )
    company = register_company(data, trade_license, db)
    token = create_access_token({"sub": company.email, "role": "company"})
    return CompanyTokenResponse(access_token=token, company=company)


@router.post("/login", response_model=CompanyTokenResponse)
def login(data: CompanyLoginRequest, db: Session = Depends(get_db)):
    company = login_company(data, db)
    token = create_access_token({"sub": company.email, "role": "company"})
    return CompanyTokenResponse(access_token=token, company=company)


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return request_company_password_reset(data.email, db)


# ---------- Needs a valid company token ----------
@router.get("/me", response_model=CompanyResponse)
def get_my_profile(company: CompanyModel = Depends(get_current_company)):
    # The frontend calls this to show the latest verification status / rejection reason
    return company


@router.put("/reupload-license", response_model=CompanyResponse)
def reupload_license(
    license_issue_date: str = Form(""),
    license_expiry_date: str = Form(""),
    trade_license: Optional[UploadFile] = File(None),
    company: CompanyModel = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    return reupload_trade_license(
        company, trade_license, license_issue_date, license_expiry_date, db
    )