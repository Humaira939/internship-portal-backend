from sqlalchemy import text

from src.utils.db import engine


# Test PostgreSQL connection
with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Database connected successfully!")