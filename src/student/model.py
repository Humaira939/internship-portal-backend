from datetime import datetime,timezone
from sqlalchemy import JSON, Column,DateTime,String,Integer
from src.utils.db import Base

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    resume_path = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc))