from datetime import datetime
from sqlalchemy import Integer, String, Column,DateTime 
from src.utils.db import Base


class CompanyModel(Base):
    __tablename__ = "companies"


    id = Column(Integer,primary_key = True, index = True)
    company_name = Column(String,nullable = False)
    email = Column(String,unique = True, index = True,nullable = False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


