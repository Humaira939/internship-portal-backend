from datetime import datetime
from pydantic import BaseModel, EmailStr


class CompanyCreateDTO(BaseModel):
    company_name: str
    email: EmailStr
    password: str


class CompanyResponseDTO(BaseModel):
    id: int
    company_name: str
    email: EmailStr
    created_at: datetime

    class config:
        from_attributes = True
    

