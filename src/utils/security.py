from datetime import datetime, timedelta, timezone
from jose import jwt
from pwdlib import PasswordHash  # Ya passlib jo bhi library aap use kar rahi hain

from src.utils.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token will expire after 1 hour

# Password Hashing Setup
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Password ko hash karne ke liye"""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Plain password aur DB wale hashed password ko compare karne ke liye"""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    # Copy data so we don't modify the original dictionary
    to_encode = data.copy()

    # Set token expiry time
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Create and return the signed JWT token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
