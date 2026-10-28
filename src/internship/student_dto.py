from datetime import date, datetime
from typing import List, Optional
 
from pydantic import BaseModel
 
 
# ============ RESPONSE: one card of the browse page ============
class StudentInternshipCard(BaseModel):
    id: int
    title: str
    category: str
    company_name: str
    work_arrangement: str                 # Remote / Hybrid / On-site
    location: str                         # "Remote" or the office city
    compensation_type: str                # Paid / Unpaid
    stipend_amount: Optional[float] = None
    stipend_currency: Optional[str] = None
    duration: str
    schedule: str
    skills: List[str] = []
    application_deadline: Optional[date] = None
    created_at: Optional[datetime] = None
    match_pct: Optional[float] = None     # AI match (empty until the AI module is connected)
    has_applied: bool = False             # becomes real when the applications module exists
 
 
# ============ RESPONSE: the browse page (cards + paging) ============
class StudentInternshipList(BaseModel):
    internships: List[StudentInternshipCard]
    total: int            # how many internships match the search and filters (all pages)
    page: int
    page_size: int
    has_more: bool        # is there a next page? (for the "Load more" button)
 
 
# ============ RESPONSE: the company part of the detail page (no private data) ============
class CompanyPublicInfo(BaseModel):
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
 
 
# ============ RESPONSE: the detail page ============
class StudentInternshipDetail(StudentInternshipCard):
    description: str
    responsibilities: str
    requirements: str
    candidate_type: str
    min_semester: Optional[int] = None
    education_level: str
    academic_background: str
    remote_region: Optional[str] = None
    remote_timezone: Optional[str] = None
    office_city: Optional[str] = None
    office_address: Optional[str] = None
    office_days: Optional[int] = None
    hours_per_week: str
    start_date: date
    positions: int
    company: CompanyPublicInfo
    can_apply: bool = True
 