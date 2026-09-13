from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from src.admin.model import AdminModel
from src.admin.router import router as admin_router
from src.auth.router import auth_router
from src.company.model import CompanyModel
from src.company.router import router as company_router
from src.student.model import StudentModel
from src.student.router import router as student_router
from src.utils.db import Base, engine

# Create tables in PostgreSQL backend for Admin, Student, and Company models
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(title="AI-Based Internship Portal API", version="1.0.0")

# Allowed origins for React frontend (Vite / Create-React-App default ports)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with main FastAPI application
app.include_router(admin_router)
app.include_router(company_router)
app.include_router(student_router)
app.include_router(auth_router)


@app.get("/ping")
def ping():
    """Health check endpoint to verify API functionality."""
    return {"message": "Internship Portal API is working"}


@app.get("/db-test")
def db_test():
    """Endpoint to verify database connectivity."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"message": "Database connected successfully"}