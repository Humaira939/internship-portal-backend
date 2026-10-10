from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ============ REQUEST: admin login ============
class AdminLoginRequest(BaseModel):
    email: str
    password: str


# ============ REQUEST: reject a company (the reason is optional) ============
class RejectCompanyRequest(BaseModel):
    reason: str = ""


# ============ RESPONSES (password_hash is never included) ============
class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse