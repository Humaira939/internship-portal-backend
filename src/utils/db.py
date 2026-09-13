from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.utils.settings import settings


# Connect FastAPI with PostgreSQL
engine = create_engine(settings.DB_CONNECTION)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all database models
Base = declarative_base()


# Provide a database session to API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()