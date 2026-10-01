from fastapi import APIRouter, Depends, HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from src.auth.dto import ResetPasswordRequest
from src.company.model import CompanyModel
from src.student.model import StudentModel
from src.utils.db import get_db
from src.utils.password_reset import verify_reset_token

router = APIRouter(prefix="/auth", tags=["Auth"])
password_hash = PasswordHash.recommended()


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    # The token tells us WHO this is and WHICH table (student/company) to update
    email, role = verify_reset_token(data.token)

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    model = StudentModel if role == "student" else CompanyModel
    user = db.query(model).filter(model.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    user.password_hash = password_hash.hash(data.new_password)
    db.commit()

    return {"message": "Your password has been reset successfully. You can now log in."}