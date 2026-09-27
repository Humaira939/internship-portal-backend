from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.utils.db import get_db
from src.company.dto import CompanySignupRequest, CompanyLoginRequest, CompanyResponse, CompanyTokenResponse
from src.company.controller import register_company, login_company
from src.utils.security import create_access_token

router = APIRouter(prefix="/company", tags=["Company"])


@router.post("/signup", response_model=CompanyResponse)
def signup(data: CompanySignupRequest, db: Session = Depends(get_db)):
    return register_company(data, db)


@router.post("/login", response_model=CompanyTokenResponse)
def login(data: CompanyLoginRequest, db: Session = Depends(get_db)):
    company = login_company(data, db)
    token = create_access_token({"sub": company.email})
    return CompanyTokenResponse(access_token=token, company=company)