from datetime import datetime, timedelta, timezone
from jose import jwt

from src.utils.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token will expire after 1 hour


def create_access_token(data: dict):
    # Copy data so we don't modify the original dictionary
    to_encode = data.copy()

    # Set token expiry time
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Create and return the signed JWT token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt