from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, String

from src.utils.db import Base


class CompanyStatus:
    """All possible verification statuses of a company (stored as text in the database)."""

    PENDING = "pending"                      # new signup / license re-upload requested / re-uploaded -> waiting for admin
    VERIFIED = "verified"                    # admin approved -> can post internships
    REJECTED = "rejected"                    # admin rejected (with a reason)
    BLOCKED = "blocked"                      # admin blocked -> cannot login or post


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

    # Admin verification: pending / verified / rejected / blocked
    # server_default makes the existing companies become "pending" automatically
    verification_status = Column(String, nullable=False, default="pending", server_default="pending")
    rejection_reason = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)