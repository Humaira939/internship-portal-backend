from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt

from src.utils.settings import settings

ALGORITHM = "HS256"
RESET_TOKEN_EXPIRE_MINUTES = 15


def create_reset_token(email: str, role: str) -> str:
    # The role is stored inside the token itself, so the reset page
    # does not need to ask the user whether they are a student or a company
    payload = {
        "sub": email,
        "role": role,
        "purpose": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_reset_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    # "purpose" check stops someone from reusing a normal login token here
    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    email = payload.get("sub")
    role = payload.get("role")
    if not email or role not in ("student", "company"):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    return email, role