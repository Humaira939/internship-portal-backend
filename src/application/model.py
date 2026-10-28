from datetime import datetime, timezone
 
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
 
from src.utils.db import Base
 
 
class ApplicationStatus:
    APPLIED = "applied"          # the student has applied (the company has not decided yet)
    SHORTLISTED = "shortlisted"  # the next statuses are used by the company's applicants page (later)
    REJECTED = "rejected"
    ACCEPTED = "accepted"
 
 
class ApplicationModel(Base):
    """A student applying to an internship.   students 1 ---- N applications N ---- 1 internships
 
    A student can apply to the same internship only once (unique rule below).
    The apply form lets the student edit their details, so every application keeps its OWN copy
    (snapshot) of the details and the resume that were sent. Later changes in the profile
    do not change an application that was already sent."""
 
    __tablename__ = "applications"
 
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    internship_id = Column(
        Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String(20), nullable=False, default="applied", server_default="applied", index=True)
 
    # ---- The details the student confirmed in the apply form (snapshot) ----
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=False)
    city = Column(String(100), nullable=False)
    university = Column(String(150), nullable=False)
    degree = Column(String(100), nullable=False)
    graduation_year = Column(String(4), nullable=True)
    cgpa = Column(Numeric(3, 2), nullable=True)
    skills = Column(JSON, nullable=True)            # the CONFIRMED skills (a list of names) - used for AI matching
    cover_note = Column(Text, nullable=True)        # "message to the company"
 
    # The resume of THIS application: a separate copy of the file
    resume_path = Column(String, nullable=False)
 
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
 
    student = relationship("StudentModel")
    internship = relationship("InternshipModel")
 
    __table_args__ = (
        UniqueConstraint("student_id", "internship_id", name="uq_application_student_internship"),
    )
 