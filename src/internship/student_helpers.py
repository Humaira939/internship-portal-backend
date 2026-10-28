"""Small pure helpers for the STUDENT pages (browse + detail): reading the filters and
turning an internship into the dictionaries the frontend needs.
No database and no FastAPI in this file, so it is easy to test."""
from typing import List, Optional
 
# The "Type" buttons of the browse page -> the value stored in the database
TYPE_FILTERS = {
    "remote": "Remote",
    "onsite": "On-site",
    "on-site": "On-site",
    "hybrid": "Hybrid",
}
 
# The "Category" dropdown of the browse page has 4 groups; each group covers one or more of the
# 11 categories of the post-internship form. Any other value is treated as the exact category name.
CATEGORY_GROUPS = {
    "web": ["Software Development"],
    "design": ["UI/UX Design"],
    "data": ["Data Science", "Artificial Intelligence"],
    "marketing": ["Marketing"],
}
 
MAX_SEARCH_WORDS = 5
MAX_WORD_LENGTH = 50
 
 
class FilterError(Exception):
    """A filter value is not valid. str(error) is shown to the student."""
 
 
# ---------------------------------------------------------------- reading the filters
def parse_type(value: Optional[str]) -> Optional[str]:
    """'all' -> None (no filter).  'onsite' -> 'On-site'."""
    value = (value or "all").strip().lower()
    if value in ("", "all"):
        return None
    if value not in TYPE_FILTERS:
        raise FilterError("Type must be one of: all, remote, onsite, hybrid.")
    return TYPE_FILTERS[value]
 
 
def parse_duration(value: Optional[str]) -> Optional[int]:
    """'all' -> None.  '3' -> 3 (months)."""
    value = (value or "all").strip().lower()
    if value in ("", "all"):
        return None
    if not value.isdigit() or not (1 <= int(value) <= 60):
        raise FilterError("Duration must be a number of months, for example 3 or 6.")
    return int(value)
 
 
def parse_location(value: Optional[str]) -> Optional[str]:
    """'all' -> None.  Otherwise 'remote' or a city name."""
    value = " ".join((value or "all").split()).lower()
    if value in ("", "all"):
        return None
    return value[:100]
 
 
def parse_category(value: Optional[str]) -> Optional[List[str]]:
    """'all' -> None.  'web' -> ['Software Development'].  'Finance' -> ['Finance'] (exact category)."""
    value = " ".join((value or "all").split())
    if value.lower() in ("", "all"):
        return None
    if value.lower() in CATEGORY_GROUPS:
        return list(CATEGORY_GROUPS[value.lower()])
    return [value[:60]]
 
 
def search_words(text: Optional[str]) -> List[str]:
    """'  React   developer ' -> ['React', 'developer'].  Every word must match somewhere."""
    words = [word[:MAX_WORD_LENGTH] for word in (text or "").split()]
    return words[:MAX_SEARCH_WORDS]
 
 
def like_pattern(word: str) -> str:
    """Makes a word safe for LIKE: a student typing % or _ must not act as a wildcard."""
    escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
 
 
# ---------------------------------------------------------------- turning an internship into a dictionary
def _number(value):
    return float(value) if value is not None else None
 
 
def location_text(internship) -> str:
    """What the card shows as the place: 'Remote' or the office city."""
    if internship.work_arrangement == "Remote":
        return "Remote"
    return internship.office_city or ""
 
 
def to_card(internship, applied_ids=frozenset(), match_pct=None) -> dict:
    """One card of the browse page."""
    return {
        "id": internship.id,
        "title": internship.title,
        "category": internship.category,
        "company_name": internship.company.company_name,
        "work_arrangement": internship.work_arrangement,
        "location": location_text(internship),
        "compensation_type": internship.compensation_type,
        "stipend_amount": _number(internship.stipend_amount),
        "stipend_currency": internship.stipend_currency,
        "duration": internship.duration,
        "schedule": internship.schedule,
        "skills": [skill.skill_name for skill in internship.skills],
        "application_deadline": internship.application_deadline,
        "created_at": internship.created_at,
        "match_pct": match_pct,                      # filled by the AI module later
        "has_applied": internship.id in applied_ids,
    }
 
 
def to_detail(internship, has_applied=False, match_pct=None) -> dict:
    """The detail page: the card + the full description + the company. Private company data
    (email, phone, contact person) is NOT included."""
    company = internship.company
    detail = to_card(internship, {internship.id} if has_applied else frozenset(), match_pct)
    detail.update(
        {
            "description": internship.description,
            "responsibilities": internship.responsibilities,
            "requirements": internship.requirements,
            "candidate_type": internship.candidate_type,
            "min_semester": internship.min_semester,
            "education_level": internship.education_level,
            "academic_background": internship.academic_background,
            "remote_region": internship.remote_region,
            "remote_timezone": internship.remote_timezone,
            "office_city": internship.office_city,
            "office_address": internship.office_address,
            "office_days": internship.office_days,
            "hours_per_week": internship.hours_per_week,
            "start_date": internship.start_date,
            "positions": internship.positions,
            "company": {
                "name": company.company_name,
                "industry": company.industry,
                "location": company.location,
                "website": company.website,
                "description": company.description,
            },
            "can_apply": not has_applied,
        }
    )
    return detail
 