from datetime import datetime
 
from pydantic import BaseModel, ConfigDict, Field, field_validator
 
 
# ============ REQUEST: admin login ============
class AdminLoginRequest(BaseModel):
    email: str
    password: str
 
 
# ============ REQUEST: reject a company OR ask for a new trade license ============
# The reason is REQUIRED (5-500 characters). It is saved in companies.rejection_reason
# and written word for word inside the email the company receives.
# (It is checked in the controller, so a missing/short reason returns {"detail": "..."} with status 400.)
class RejectCompanyRequest(BaseModel):
    reason: str = Field(
        default="",
        description="Why the company is rejected. Emailed to the company.",
        examples=["License expiry date mismatch with the PDF document"],
    )
 
    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value):
        return value.strip() if isinstance(value, str) else value
 
 
class RequestReuploadRequest(BaseModel):
    reason: str = Field(
        default="",
        description="Why a new trade license is needed. Emailed to the company.",
        examples=["Your trade license has expired. Please upload a valid, updated copy."],
    )
 
    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value):
        return value.strip() if isinstance(value, str) else value
 
 
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
 