from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Integer, JSON
from src.utils.db import Base


class StudentModel(Base):
    __tablename__ = "students"

    # Signup fields (existing — do not touch)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Profile Setup fields (new)
    phone = Column(String, nullable=True)
    university = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    graduation_status = Column(String, nullable=True)   # "yes" or "no"
    semester = Column(String, nullable=True)
    graduation_year = Column(String, nullable=True)
    graduation_date = Column(DateTime, nullable=True)
    skills = Column(JSON, nullable=True)
    location = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    portfolio = Column(String, nullable=True)

    # Resume (used later, when we build file upload)
    resume_path = Column(String, nullable=True)
    resume_text = Column(String, nullable=True)    