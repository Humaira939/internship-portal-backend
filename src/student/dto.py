from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Schema for incoming student registration request
class StudentCreateDTO(BaseModel):
    name: str
    email: EmailStr
    password: str


# Schema for outgoing student registration response (Password excluded for security)
class StudentResponseDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    resume_path: Optional[str] = None
    skills: Optional[list] = []
    created_at: datetime

    # Enable ORM mode for SQLAlchemy model compatibility
    class Config:
        from_attributes = True

    