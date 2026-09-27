from sqlalchemy.orm import Session
from fastapi import HTTPException
from pwdlib import PasswordHash

from src.company.model import CompanyModel
from src.company.dto import CompanySignupRequest, CompanyLoginRequest

# Used to securely hash and verify passwords
password_hash = PasswordHash.recommended()


def register_company(data: CompanySignupRequest, db: Session):
    # Check if email is already registered
    existing_company = db.query(CompanyModel).filter(CompanyModel.email == data.email).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before saving (never save plain text password)
    hashed_password = password_hash.hash(data.password)

    # Create new company record
    new_company = CompanyModel(
        company_name=data.company_name,
        email=data.email,
        password_hash=hashed_password
    )

    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return new_company


def login_company(data: CompanyLoginRequest, db: Session):
    # Find company by email
    company = db.query(CompanyModel).filter(CompanyModel.email == data.email).first()
    if not company:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password against stored hash
    if not password_hash.verify(data.password, company.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return company