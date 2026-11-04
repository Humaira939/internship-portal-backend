"""The rate limit RULES: which requests are limited, and how much. (Plain Python: no FastAPI, easy to test.)
 
A rule says: "at most <limit> requests in <window> seconds from one IP address".
The first rule that matches a request is used, so the specific rules come before the general one.
To change a limit, only change the numbers in the table below.
"""
import re
from dataclasses import dataclass
from typing import Optional
 
MINUTE = 60
HOUR = 3600
 
 
@dataclass(frozen=True)
class Rule:
    name: str        # the group (the counter is kept per IP and per group)
    limit: int       # how many requests ...
    window: int      # ... in how many seconds
 
 
# ----------------------------------------------------------------------------- the rules
LOGIN = Rule("login", 10, MINUTE)          # stops password guessing
SIGNUP = Rule("signup", 10, HOUR)          # stops fake accounts
PASSWORD = Rule("password", 5, HOUR)       # forgot / reset password: stops email bombing
CONTACT = Rule("contact", 10, HOUR)        # the contact form (the form also has its own stricter limit)
APPLY = Rule("apply", 30, HOUR)            # applying to internships
API = Rule("api", 120, MINUTE)             # every other API request
 
# (the HTTP method, the path pattern, the rule)   - the FIRST match wins
RULES = [
    ("POST", re.compile(r"^/(student|company|admin|auth)/login$"), LOGIN),
    ("POST", re.compile(r"^/(student|company)/signup$"), SIGNUP),
    ("POST", re.compile(r"(forgot|reset)[-_]?password"), PASSWORD),
    ("POST", re.compile(r"^/contact$"), CONTACT),
    ("POST", re.compile(r"^/student/applications$"), APPLY),
]
 
# Only these parts of the site are the API. Pages (/login, /student-dashboard, ...), /css, /js, /images,
# /docs and /health are not counted at all.
API_PREFIXES = ("/student", "/company", "/admin", "/auth", "/contact")
 
 
def normalize(path: str) -> str:
    """'/student/login/' -> '/student/login'"""
    if len(path) > 1 and path.endswith("/"):
        return path.rstrip("/")
    return path
 
 
def is_api_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in API_PREFIXES)
 
 
def find_rule(method: str, path: str) -> Optional[Rule]:
    """The rule for this request, or None when the request is not limited."""
    method = method.upper()
    path = normalize(path)
 
    # The browser's CORS "preflight" check (OPTIONS) is not a real request: never counted
    if method == "OPTIONS":
        return None
 
    if not is_api_path(path):
        return None
 
    for rule_method, pattern, rule in RULES:
        if method == rule_method and pattern.search(path):
            return rule
 
    return API
 