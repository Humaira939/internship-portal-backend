from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

# Password Hashing Setup (Argon2)
pwd_context = PasswordHash.recommended()

# JWT Configuration
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_HERE"  # Production mein .env file se aayega
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours TTL


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Plain password ko hashed password se verify karta hai."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Password ko Argon2 algorithim ke sath hash karta hai."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Payload (user data + role) ko encode karke stateless JWT token banata hai."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
