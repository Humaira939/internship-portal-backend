from typing import Optional
 
from pydantic import BaseModel
 
 
# ============ REQUEST: the contact form (the keys that contact.js sends) ============
# Every rule is checked in contact/validators.py.
class ContactRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    topic: Optional[str] = None
    message: Optional[str] = None
 
 
# ============ RESPONSE ============
class ContactResponse(BaseModel):
    message: str
 