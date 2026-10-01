from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.company.router import router as company_router
from src.student.router import router as student_router
from src.utils.db import Base, engine

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

# Register routes
app.include_router(student_router)
app.include_router(company_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "SmartIntern API is running"}