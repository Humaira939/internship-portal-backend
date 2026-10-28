from datetime import datetime
from typing import List, Optional, Union
 
from pydantic import AliasChoices, BaseModel, Field
 
 
# ============ REQUEST: apply to an internship (JSON) ============
# The names are the ones the apply form (apply-flow.js) already sends:
# internshipId / full_name / email / phone / city / university / degree / graduation_year / cgpa / skills / cover_note.
# Extra keys (internshipTitle, company) are ignored. Every rule is checked in application/validators.py.
class ApplyRequest(BaseModel):
    internship_id: int = Field(validation_alias=AliasChoices("internship_id", "internshipId"))
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    university: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Union[str, int, None] = None
    cgpa: Union[str, int, float, None] = None
    skills: Optional[List[str]] = None
    cover_note: Optional[str] = None
 
 
# ============ RESPONSE: the application that was just submitted ============
class ApplicationResponse(BaseModel):
    id: int
    internship_id: int
    internship_title: str
    company_name: str
    status: str
    applied_at: Optional[datetime] = None
 