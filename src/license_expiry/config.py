"""One place for every value used by the license expiry module.
 
The values are read from utils/settings.py when they exist there (LICENSE_TIMEZONE, GRACE_PERIOD_DAYS,
FRONTEND_UPLOAD_URL, LICENSE_CHECK_ON_STARTUP); otherwise the defaults below are used.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo
 
from src.utils.settings import settings
 
# ---------------- values (override them in utils/settings.py) ----------------
TIMEZONE = getattr(settings, "LICENSE_TIMEZONE", "Asia/Karachi")
GRACE_PERIOD_DAYS = int(getattr(settings, "GRACE_PERIOD_DAYS", 28))
FRONTEND_UPLOAD_URL = getattr(
    settings, "FRONTEND_UPLOAD_URL", "http://127.0.0.1:5500/html/company-profile.html"
)
CHECK_ON_STARTUP = bool(getattr(settings, "LICENSE_CHECK_ON_STARTUP", True))
 
# A verified company may upload a renewal license when its license has 7 days or less left
RENEWAL_WINDOW_DAYS = 7
 
# ---------------- milestone names (used in the log table and the emails) ----------------
D_MINUS_7 = "D-7"
D_MINUS_3 = "D-3"
D_ZERO = "D0"
PLUS_14 = "+14"
PLUS_25 = "+25"
FROZEN = "FROZEN"
 
 
def today_local() -> date:
    """'Today' in the one configured timezone, so every part of the project agrees on the date."""
    return datetime.now(ZoneInfo(TIMEZONE)).date()
 