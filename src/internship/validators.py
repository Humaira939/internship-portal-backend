"""All the rules for a new internship, in plain Python (no database, no FastAPI).
 
The controller calls validate_and_clean(). It returns clean values ready to be saved,
or raises InternshipValidationError with a message that is shown to the company.
The frontend also validates, but the backend never trusts the frontend.
"""
import math
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
 
# ---- The exact values of the dropdowns in post-internship.html ----
CATEGORIES = (
    "Software Development", "Artificial Intelligence", "Data Science", "UI/UX Design",
    "Cybersecurity", "Marketing", "Business", "Human Resources", "Finance",
    "Content Writing", "Other",
)
CANDIDATE_TYPES = ("Current student", "Fresh graduate", "Graduate", "Any")
EDUCATION_LEVELS = ("High School", "Diploma", "Undergraduate", "Graduate", "Any")
WORK_ARRANGEMENTS = ("Remote", "Hybrid", "On-site")
SCHEDULES = ("Full-time", "Part-time")
HOURS_PER_WEEK = ("Up to 10 hours", "11–20 hours", "21–30 hours", "31–40 hours", "40+ hours")
COMPENSATION_TYPES = ("Paid", "Unpaid")
CURRENCIES = ("PKR", "USD", "GBP", "EUR")
 
# ---- Limits ----
TITLE_MIN, TITLE_MAX = 3, 150
LONG_TEXT_MIN, LONG_TEXT_MAX = 10, 5000
MAX_POSITIONS = 1000
MAX_SKILLS, SKILL_MAX = 30, 50
ACADEMIC_MAX = 150
PLACE_MAX, ADDRESS_MAX, TIMEZONE_MAX = 100, 255, 60
DURATION_MAX = 40
MAX_STIPEND = 100_000_000
MAX_DAYS_AHEAD = 730          # start date may be at most 2 years away (catches typing mistakes)
 
 
class InternshipValidationError(Exception):
    """A rule was broken. str(error) is the message for the company."""
 
 
def fail(message: str):
    raise InternshipValidationError(message)
 
 
# ---------------------------------------------------------------- text helpers
def one_line(value) -> str:
    """Removes extra spaces and line breaks: '  Data   Science ' -> 'Data Science'."""
    return " ".join(str(value or "").split())
 
 
def long_text(value) -> str:
    """Keeps line breaks (descriptions have paragraphs) but removes empty space around the text."""
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text
 
 
def pick(value, allowed, message):
    value = one_line(value)
    if value not in allowed:
        fail(message)
    return value
 
 
def parse_date(value, label) -> date:
    try:
        return datetime.strptime(one_line(value), "%Y-%m-%d").date()
    except ValueError:
        fail(f"{label} is not valid.")
 
 
def clean_skills(raw):
    """['Python', ' python ', 'SQL'] -> [('Python', 'python'), ('SQL', 'sql')]  (duplicates removed)"""
    if not isinstance(raw, (list, tuple)):
        fail("Please add the required skills.")
 
    seen, result = set(), []
    for item in raw:
        name = one_line(item)
        if not name:
            continue
        if len(name) > SKILL_MAX:
            fail(f"Each skill must be {SKILL_MAX} characters or fewer.")
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append((name, key))
 
    if not result:
        fail("Please add at least one required skill.")
    if len(result) > MAX_SKILLS:
        fail(f"You can add up to {MAX_SKILLS} skills.")
    return result
 
 
# ---------------------------------------------------------------- the main function
def validate_and_clean(data, today: date, existing_start=None, existing_deadline=None) -> dict:
    """data: any object with the request fields. today: today's date (Asia/Karachi).
 
    existing_start / existing_deadline are only used when EDITING: if the company does not change
    a date that is already in the past, it is accepted (an old internship can still be edited).
    A NEW date must always be today or later."""
    values = {}
 
    # ---- 1. Basic information ----
    title = one_line(data.title)
    if not (TITLE_MIN <= len(title) <= TITLE_MAX):
        fail(f"Internship title must be {TITLE_MIN} to {TITLE_MAX} characters.")
    values["title"] = title
 
    values["category"] = pick(data.category, CATEGORIES, "Please select a valid category.")
 
    positions = data.positions
    if isinstance(positions, bool) or not isinstance(positions, int) or not (1 <= positions <= MAX_POSITIONS):
        fail(f"Number of positions must be between 1 and {MAX_POSITIONS}.")
    values["positions"] = positions
 
    for field, label in (
        ("description", "internship description"),
        ("responsibilities", "key responsibilities"),
        ("requirements", "requirements"),
    ):
        text = long_text(getattr(data, field))
        if not (LONG_TEXT_MIN <= len(text) <= LONG_TEXT_MAX):
            fail(f"Please write the {label} ({LONG_TEXT_MIN} to {LONG_TEXT_MAX} characters).")
        values[field] = text
 
    skills = clean_skills(data.skills)
 
    # ---- 2. Who can apply ----
    values["candidate_type"] = pick(data.candidate_type, CANDIDATE_TYPES, "Please select who can apply.")
 
    if values["candidate_type"] == "Current student":
        semester = data.min_semester
        if isinstance(semester, bool) or not isinstance(semester, int) or not (1 <= semester <= 8):
            fail("Please select the minimum semester (1 to 8).")
        values["min_semester"] = semester
    else:
        values["min_semester"] = None          # the semester only matters for current students
 
    values["education_level"] = pick(data.education_level, EDUCATION_LEVELS, "Please select the minimum education level.")
 
    academic = one_line(data.academic_background)
    if not (1 <= len(academic) <= ACADEMIC_MAX):
        fail("Please enter the preferred academic background.")
    values["academic_background"] = academic
 
    # ---- 3. Work arrangement (the fields depend on the choice) ----
    arrangement = pick(data.work_arrangement, WORK_ARRANGEMENTS, "Please select the work arrangement.")
    values["work_arrangement"] = arrangement
 
    region = one_line(data.remote_region)
    timezone_text = one_line(data.remote_timezone)
    city = one_line(data.office_city)
    address = one_line(data.office_address)
    days = data.office_days
 
    if arrangement == "Remote":
        if not region:
            fail("Please enter the eligible country or region.")
        if not timezone_text:
            fail("Please enter the expected time zone.")
        if len(region) > PLACE_MAX or len(timezone_text) > TIMEZONE_MAX:
            fail("The region or time zone is too long.")
        values.update(remote_region=region, remote_timezone=timezone_text,
                      office_city=None, office_address=None, office_days=None)
    else:
        if not city:
            fail("Please enter the office city.")
        if not address:
            fail("Please enter the office address.")
        if len(city) > PLACE_MAX or len(address) > ADDRESS_MAX:
            fail("The office city or address is too long.")
        if arrangement == "Hybrid":
            if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= 4):
                fail("Please select the office days per week (1 to 4).")
        else:
            days = None
        values.update(remote_region=None, remote_timezone=None,
                      office_city=city, office_address=address, office_days=days)
 
    # ---- 4. Duration, schedule, compensation ----
    duration = one_line(data.duration)
    if not duration or duration == "Other":
        fail("Please specify the internship duration.")
    if len(duration) > DURATION_MAX:
        fail(f"Duration must be {DURATION_MAX} characters or fewer.")
    values["duration"] = duration
 
    values["schedule"] = pick(data.schedule, SCHEDULES, "Please select the work schedule.")
    values["hours_per_week"] = pick(data.hours_per_week, HOURS_PER_WEEK, "Please select the weekly hours.")
 
    compensation = pick(data.compensation_type, COMPENSATION_TYPES, "Please select the compensation type.")
    values["compensation_type"] = compensation
 
    if compensation == "Paid":
        amount = data.stipend_amount
        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount <= 0
        ):
            fail("Please enter the stipend amount (more than 0).")
        if amount > MAX_STIPEND:
            fail("The stipend amount is too large.")
        currency = pick(data.stipend_currency, CURRENCIES, "Please select the stipend currency.")
        values["stipend_amount"] = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        values["stipend_currency"] = currency
    else:
        values["stipend_amount"] = None        # an unpaid internship has no stipend
        values["stipend_currency"] = None
 
    # ---- 5. Dates ----
    start_text = one_line(data.start_date)
    if not start_text:
        fail("Please select the expected start date.")
    start = parse_date(start_text, "Start date")
    if start < today and start != existing_start:
        fail("Start date cannot be in the past.")
    if start > today + timedelta(days=MAX_DAYS_AHEAD):
        fail("Start date is too far in the future.")
    values["start_date"] = start
 
    deadline_text = one_line(data.application_deadline)
    if deadline_text:
        deadline = parse_date(deadline_text, "Application deadline")
        if deadline < today and deadline != existing_deadline:
            fail("Application deadline cannot be in the past.")
        if deadline > start:
            fail("Application deadline must be on or before the start date.")
        values["application_deadline"] = deadline
    else:
        values["application_deadline"] = None
 
    values["skills"] = skills
    return values