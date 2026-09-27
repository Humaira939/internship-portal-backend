from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.db import Base, engine
from src.student.router import router as student_router
from src.company.router import router as company_router

# Create all database tables (if they don't already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartIntern API")

# Allow frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only — restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register student routes (signup, login)
app.include_router(student_router)

# Register company routes (signup, login)
app.include_router(company_router)


@app.get("/")
def root():
    return {"message": "SmartIntern API is running"}