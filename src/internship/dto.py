from datetime import date, datetime
from typing import List, Optional
 
from pydantic import BaseModel, ConfigDict, field_validator
 
 
# ============ REQUEST: post a new internship ============
# The field names are EXACTLY the keys sent by post-internship.js (buildInternshipPayload),
# so the frontend does not have to change anything.
# The values are only read here; every rule is checked in internship/validators.py.
class InternshipCreateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    positions: Optional[int] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    candidate_type: Optional[str] = None
    min_semester: Optional[int] = None
    education_level: Optional[str] = None
    academic_background: Optional[str] = None
    work_arrangement: Optional[str] = None
    remote_region: Optional[str] = None
    remote_timezone: Optional[str] = None
    office_city: Optional[str] = None
    office_address: Optional[str] = None
    office_days: Optional[int] = None
    duration: Optional[str] = None
    schedule: Optional[str] = None
    hours_per_week: Optional[str] = None
    compensation_type: Optional[str] = None
    stipend_amount: Optional[float] = None
    stipend_currency: Optional[str] = None
    start_date: Optional[str] = None                # YYYY-MM-DD
    application_deadline: Optional[str] = None      # YYYY-MM-DD (optional)
 
 
# ============ REQUEST: edit an internship (all fields again, same rules as posting) ============
class InternshipUpdateRequest(InternshipCreateRequest):
    pass
 
 
# ============ RESPONSE: one internship ============
class InternshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    company_id: int
    title: str
    category: str
    positions: int
    description: str
    responsibilities: str
    requirements: str
    skills: List[str] = []
    candidate_type: str
    min_semester: Optional[int] = None
    education_level: str
    academic_background: str
    work_arrangement: str
    remote_region: Optional[str] = None
    remote_timezone: Optional[str] = None
    office_city: Optional[str] = None
    office_address: Optional[str] = None
    office_days: Optional[int] = None
    duration: str
    schedule: str
    hours_per_week: str
    compensation_type: str
    stipend_amount: Optional[float] = None
    stipend_currency: Optional[str] = None
    start_date: date
    application_deadline: Optional[date] = None
    status: str
    applicants_count: int = 0          # becomes real when the applications module exists
    deadline_passed: bool = False      # the application deadline is over (students no longer see it)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
 
    # The database stores skills as rows (InternshipSkillModel); the frontend gets a plain list of names
    @field_validator("skills", mode="before")
    @classmethod
    def skills_as_names(cls, value):
        return [getattr(item, "skill_name", item) for item in (value or [])]
 
    # Numeric columns come back as Decimal, but JSON should contain a normal number
    @field_validator("stipend_amount", mode="before")
    @classmethod
    def amount_as_number(cls, value):
        return float(value) if value is not None else None
 
 
# ============ RESPONSE: the company's list of internships (Manage Internships page) ============
class InternshipStats(BaseModel):
    total: int = 0
    active: int = 0
    draft: int = 0
    closed: int = 0
    applicants: int = 0
 
 
class InternshipListResponse(BaseModel):
    internships: List[InternshipResponse]
    stats: InternshipStats
 