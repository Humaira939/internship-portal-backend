from datetime import datetime, timezone
 
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
 
from src.license_expiry.config import today_local
from src.utils.db import Base
 
 
class InternshipStatus:
    DRAFT = "draft"      # saved but not published (not visible to students)
    ACTIVE = "active"    # published
    CLOSED = "closed"    # no longer accepting applications
 
 
class InternshipModel(Base):
    """One internship posted by a company.   companies 1 ---- N internships"""
 
    __tablename__ = "internships"
 
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
 
    # ---- Basic information ----
    title = Column(String(150), nullable=False)
    category = Column(String(60), nullable=False)
    positions = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    responsibilities = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
 
    # ---- Who can apply ----
    candidate_type = Column(String(30), nullable=False)       # Current student / Fresh graduate / ...
    min_semester = Column(Integer, nullable=True)             # only for "Current student"
    education_level = Column(String(40), nullable=False)
    academic_background = Column(String(150), nullable=False)
 
    # ---- Work arrangement ----
    work_arrangement = Column(String(20), nullable=False)     # Remote / Hybrid / On-site
    remote_region = Column(String(100), nullable=True)        # only Remote
    remote_timezone = Column(String(60), nullable=True)       # only Remote
    office_city = Column(String(100), nullable=True)          # Hybrid / On-site
    office_address = Column(String(255), nullable=True)       # Hybrid / On-site
    office_days = Column(Integer, nullable=True)              # only Hybrid
 
    # ---- Duration and compensation ----
    duration = Column(String(40), nullable=False)
    schedule = Column(String(20), nullable=False)             # Full-time / Part-time
    hours_per_week = Column(String(40), nullable=False)
    compensation_type = Column(String(10), nullable=False)    # Paid / Unpaid
    stipend_amount = Column(Numeric(12, 2), nullable=True)    # only Paid
    stipend_currency = Column(String(3), nullable=True)       # only Paid
 
    # ---- Dates ----
    start_date = Column(Date, nullable=False)
    application_deadline = Column(Date, nullable=True)
 
    # ---- Status and timestamps ----
    status = Column(String(20), nullable=False, default="active", server_default="active", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    closed_at = Column(DateTime, nullable=True)
 
    # The company that posted it (used by the student pages to show the company name and details)
    company = relationship("CompanyModel")
 
    # Required skills (rows of the internship_skills table); deleted together with the internship
    skills = relationship(
        "InternshipSkillModel",
        cascade="all, delete-orphan",
        order_by="InternshipSkillModel.id",
    )
 
    # Calculated value (not a column): the frontend shows "deadline passed" on the card
    @property
    def deadline_passed(self):
        return self.application_deadline is not None and self.application_deadline < today_local()
 
 
class InternshipSkillModel(Base):
    """One required skill of one internship.   internships 1 ---- N internship_skills
 
    skill_name = the text to show ("Python")
    skill_key  = lower-case version used for comparing ("python"): matching students, analytics, duplicates
    """
 
    __tablename__ = "internship_skills"
 
    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(
        Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_name = Column(String(50), nullable=False)
    skill_key = Column(String(50), nullable=False, index=True)
 
    __table_args__ = (
        UniqueConstraint("internship_id", "skill_key", name="uq_internship_skill_once"),
    )
 