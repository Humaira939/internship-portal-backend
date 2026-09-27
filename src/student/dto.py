from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


# ==========================================================
# REQUEST SCHEMA: Data coming FROM frontend during Signup
# ==========================================================
class StudentSignupRequest(BaseModel):
    name: str              # Matches frontend field: fullName
    email: EmailStr        # Matches frontend field: email
    password: str          # Matches frontend field: password
    confirm_password: str  # Matches frontend field: confirmPassword

    # Custom validation: password must be at least 6 characters
    @field_validator("password")
    @classmethod
    def password_length(cls, value):
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value

    # Custom validation: password and confirm_password must match
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value, info):
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


# ==========================================================
# REQUEST SCHEMA: Data coming FROM frontend during Login
# ==========================================================
class StudentLoginRequest(BaseModel):
    email: EmailStr        # Matches frontend field: email
    password: str          # Matches frontend field: password


# ==========================================================
# RESPONSE SCHEMA: Data sent BACK to frontend after Signup
# Note: password_hash is NEVER included here (security)
# ==========================================================
class StudentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy model to this schema


# ==========================================================
# RESPONSE SCHEMA: Data sent BACK to frontend after Login
# Includes a token so the frontend can stay "logged in"
# ==========================================================
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentResponse