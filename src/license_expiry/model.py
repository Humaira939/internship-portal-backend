from datetime import datetime, timezone
 
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
 
from src.utils.db import Base
 
 
class LicenseReminderLog(Base):
    """One row = one milestone email sent for one license (one expiry date) of one company.
 
    The unique constraint makes the daily job safe to run twice: the same email can never be
    sent twice. A renewed license has a NEW expiry date, so its reminder cycle starts fresh.
    """
 
    __tablename__ = "license_reminder_log"
 
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    license_expiry_date = Column(Date, nullable=False)
    milestone = Column(String(10), nullable=False)   # D-7, D-3, D0, +14, +25, FROZEN
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
 
    __table_args__ = (
        UniqueConstraint(
            "company_id", "license_expiry_date", "milestone",
            name="uq_license_reminder_company_expiry_milestone",
        ),
    )
 