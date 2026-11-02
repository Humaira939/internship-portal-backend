"""Rules for the contact form (plain Python: no database, no FastAPI).
The frontend checks the same things, but the backend never trusts the frontend."""
import hashlib
import re
 
EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\+?[0-9\s\-]{7,20}$"
 
# The exact values of the two dropdowns in index.html
ROLES = ("student", "company", "other")
TOPICS = {
    "general": "General question",
    "account": "Account or login problem",
    "internship": "Internships and applications",
    "company": "Company verification",
    "technical": "Report a technical issue",
    "feedback": "Feedback or suggestion",
}
 
NAME_MIN, NAME_MAX = 2, 80
EMAIL_MAX = 120
MESSAGE_MIN, MESSAGE_MAX = 10, 1000
 
 
class ContactValidationError(Exception):
    """A rule was broken. str(error) is the message for the visitor."""
 
 
def fail(message: str):
    raise ContactValidationError(message)
 
 
def one_line(value) -> str:
    """Removes extra spaces and line breaks (this also makes header injection impossible)."""
    return " ".join(str(value if value is not None else "").split())
 
 
def message_text(value) -> str:
    text = str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n").strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text
 
 
def fingerprint(email: str, message: str) -> str:
    """A short code of 'this email + this message'. Used to stop the same message being sent again and again."""
    normal = " ".join(message.lower().split())
    return hashlib.sha256(f"{email}|{normal}".encode("utf-8")).hexdigest()
 
 
def validate_contact(data) -> dict:
    values = {}
 
    name = one_line(data.name)
    if not (NAME_MIN <= len(name) <= NAME_MAX):
        fail("Please enter your name.")
    values["name"] = name
 
    email = one_line(data.email).lower()
    if not re.match(EMAIL_PATTERN, email) or len(email) > EMAIL_MAX:
        fail("Please enter a valid email.")
    values["email"] = email
 
    phone = one_line(data.phone)
    if phone:
        if not re.match(PHONE_PATTERN, phone) or len(re.sub(r"\D", "", phone)) < 10:
            fail("Please enter a valid phone number.")
        values["phone"] = phone
    else:
        values["phone"] = None
 
    role = one_line(data.role).lower() or "other"
    if role not in ROLES:
        fail("Please choose who you are: student, company or other.")
    values["role"] = role
 
    topic = one_line(data.topic).lower()
    if topic not in TOPICS:
        fail("Please choose a topic.")
    values["topic"] = topic
 
    message = message_text(data.message)
    if len(message) < MESSAGE_MIN:
        fail(f"Please write at least {MESSAGE_MIN} characters.")
    if len(message) > MESSAGE_MAX:
        fail(f"Your message must be {MESSAGE_MAX} characters or fewer.")
    values["message"] = message
 
    values["message_hash"] = fingerprint(email, message)
    return values
 