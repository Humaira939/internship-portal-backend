from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.auth.dto import LoginDTO, TokenResponseDTO
from src.student.model import StudentModel
from src.company.model import CompanyModel
from src.utils.security import create_access_token,verify_password

def authenticate_user(db: Session, login_data: LoginDTO) -> TokenResponseDTO:
    """Authenticates student or company user credentials and returns a JWT access token."""

    # 1. Check in Student Table
    student = (db.query(StudentModel).filter(StudentModel.email == login_data.email)).first()
    if student:
        if not verify_password(login_data.password ,student.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid email or password",
            )
        token_payload ={
            "id": student.id,
            "email": student.email,
            "role":"student",
        }

        token = create_access_token(data = token_payload)

        return TokenResponseDTO(
            access_token= token,
            token_type= "bearer",
            role= "student",
            user_id= student.id,
        )


    # 2. Check in Company Table
    company = (
        db.query(CompanyModel)
        .filter(CompanyModel.email == login_data.email)
        .first()
    )
    if company:
        if not verify_password(login_data.password, company.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token_payload = {
            "id": company.id,
            "email": company.email,
            "role": "company",
        }
        token = create_access_token(data=token_payload)

        return TokenResponseDTO(
            access_token=token,
            token_type="bearer",
            role="company",
            user_id=company.id,
        )

    # 3. If email is not found in both tables
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )
