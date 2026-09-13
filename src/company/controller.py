from fastapi import HTTPException,status
from pwdlib import PasswordHash
from src.company.dto import CompanyCreateDTO
from sqlalchemy.orm import Session
from src.company.model import CompanyModel

password_hash = PasswordHash.recommended()


def create_company(body:CompanyCreateDTO,db:Session):
    existing_company = (
        db.query(CompanyModel).filter(CompanyModel.email == body.email).first()
    )
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this email already exists.",
        )

    hashed_password = password_hash.hash(body.password)

    new_company = CompanyModel(
        company_name = body.company_name,
        email = body.email,
        password_hash = hashed_password,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company