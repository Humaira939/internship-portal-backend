from sqlalchemy import Column, Integer, String

from src.utils.db import Base


# Admin database table
class AdminModel(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)