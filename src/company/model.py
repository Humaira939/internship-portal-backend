from datetime import date, datetime, timedelta, timezone
 
from sqlalchemy import Column, Date, DateTime, Integer, String
 
from src.license_expiry.config import GRACE_PERIOD_DAYS, today_local
from src.utils.db import Base
 
 
class CompanyStatus:
    """All possible verification statuses of a company (stored as text in the database)."""
 
    PENDING = "pending"                      # new signup / license re-upload requested / re-uploaded -> waiting for admin
    VERIFIED = "verified"                    # admin approved -> can post internships
    REJECTED = "rejected"                    # admin rejected (with a reason)
    BLOCKED = "blocked"                      # admin blocked -> cannot login or post
    FROZEN = "frozen"                        # license expired and the 28-day grace period is over
                                             # (can login + upload a new license, cannot post)
 
 
class CompanyModel(Base):
    __tablename__ = "companies"
 
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
 
    # Registration details
    industry = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    description = Column(String, nullable=True)
 
    # Trade license (file path in the private Supabase bucket + dates)
    trade_license_path = Column(String, nullable=True)
    license_issue_date = Column(Date, nullable=True)
    license_expiry_date = Column(Date, nullable=True)
 
    # Admin verification: pending / verified / rejected / blocked / frozen
    # server_default makes the existing companies become "pending" automatically
    verification_status = Column(String, nullable=False, default="pending", server_default="pending")
    rejection_reason = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
 
    # ---- Calculated values (not database columns): used by the frontend for the license banner ----
    @property
    def license_days_left(self):
        """Days until the license expires. Negative = days since it expired. None = no expiry date."""
        if self.license_expiry_date is None:
            return None
        return (self.license_expiry_date - today_local()).days
 
    @property
    def grace_ends_on(self):
        """The day the account is frozen if no valid license is uploaded."""
        if self.license_expiry_date is None:
            return None
        return self.license_expiry_date + timedelta(days=GRACE_PERIOD_DAYS)
 