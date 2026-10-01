from pydantic import BaseModel, EmailStr
from pydantic import BaseModel


class LoginDTO(BaseModel):
    """Data transfer object for validating user login requests."""
    email: EmailStr
    password: str

class TokenResponseDTO(BaseModel):
    """Data transfer object for returning authentication tokens to the client."""
    access_token: str
    token_type: str= "bearer"
    role: str
    user_id: int

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    
