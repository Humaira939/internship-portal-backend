from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from src.company.controller import login_company, register_company
from src.company.dto import (
    CompanyLoginRequest,
    CompanySignupRequest,
    CompanyTokenResponse,
)
from src.utils.db import get_db
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