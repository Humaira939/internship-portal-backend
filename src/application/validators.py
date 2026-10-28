"""Rules for the details a student sends with an application (plain Python: no database, no FastAPI).
 
The apply form lets the student change their details for THIS application, so the backend
checks every value again and saves a snapshot of it."""
import math
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
 
EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\+?[0-9\s\-]{7,20}$"      # the same rule as the student signup
 
NAME_MIN, NAME_MAX = 2, 100
EMAIL_MAX = 120
CITY_MAX, UNIVERSITY_MAX, DEGREE_MAX = 100, 150, 100
NOTE_MAX = 600
MAX_SKILLS, SKILL_MAX = 30, 50
CGPA_MAX = 4.5
 
 
class ApplicationValidationError(Exception):
    """A rule was broken. str(error) is the message for the student."""
 
 
def fail(message: str):
    raise ApplicationValidationError(message)
 
 
def one_line(value) -> str:
    return " ".join(str(value if value is not None else "").split())
 
 
def note_text(value) -> str:
    text = str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n").strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text
 
 
def clean_skills(raw) -> list:
    """['Python', ' python ', 'SQL', ''] -> ['Python', 'SQL']"""
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)):
        fail("Skills must be a list.")
 
    seen, result = set(), []
    for item in raw:
        name = one_line(item)
        if not name:
            continue
        if len(name) > SKILL_MAX:
            fail(f"Each skill must be {SKILL_MAX} characters or fewer.")
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
 
    if len(result) > MAX_SKILLS:
        fail(f"You can add up to {MAX_SKILLS} skills.")
    return result
 
 
def validate_application(data, today: date) -> dict:
    values = {}
 
    name = one_line(data.full_name)
    if not (NAME_MIN <= len(name) <= NAME_MAX):
        fail("Please enter your full name.")
    values["full_name"] = name
 
    email = one_line(data.email).lower()
    if not re.match(EMAIL_PATTERN, email) or len(email) > EMAIL_MAX:
        fail("Please enter a valid email address.")
    values["email"] = email
 
    phone = one_line(data.phone)
    if not re.match(PHONE_PATTERN, phone):
        fail("Please enter a valid phone number.")
    values["phone"] = phone
 
    for field, label, limit in (
        ("city", "your city", CITY_MAX),
        ("university", "your university", UNIVERSITY_MAX),
        ("degree", "your degree or program", DEGREE_MAX),
    ):
        text = one_line(getattr(data, field))
        if not text:
            fail(f"Please enter {label}.")
        if len(text) > limit:
            fail(f"{label[0].upper() + label[1:]} must be {limit} characters or fewer.")
        values[field] = text
 
    # Graduation year is optional
    year_text = one_line(data.graduation_year)
    if year_text:
        if not year_text.isdigit() or len(year_text) != 4 or not (1980 <= int(year_text) <= today.year + 10):
            fail("Please enter a valid graduation year.")
        values["graduation_year"] = year_text
    else:
        values["graduation_year"] = None
 
    # CGPA is optional
    cgpa_text = one_line(data.cgpa)
    if cgpa_text:
        try:
            cgpa = float(cgpa_text)
        except ValueError:
            fail("CGPA should be a number.")
        if not math.isfinite(cgpa) or not (0 <= cgpa <= CGPA_MAX):
            fail(f"CGPA should be between 0 and {CGPA_MAX}.")
        values["cgpa"] = Decimal(str(cgpa)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        values["cgpa"] = None
 
    values["skills"] = clean_skills(data.skills)
 
    note = note_text(data.cover_note)
    if len(note) > NOTE_MAX:
        fail(f"The message to the company must be {NOTE_MAX} characters or fewer.")
    values["cover_note"] = note or None
 
    return values
 