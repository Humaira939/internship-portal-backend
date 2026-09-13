from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from src.admin.dto import AdminSchema
from src.admin.model import AdminModel

# Aap ki practice wala pwdlib setup
password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# Admin creation logic
def create_admin(data: AdminSchema, db: Session):
    is_admin = (
        db.query(AdminModel).filter(AdminModel.username == data.username).first())

    if is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exist..",
        )

    # Password hashing using pwdlib
    hash_password = get_password_hash(data.password)

    new_admin = AdminModel(
        username=data.username, password_hash=hash_password
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin