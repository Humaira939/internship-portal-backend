from contextlib import asynccontextmanager
 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from src.auth.router import router as auth_router
from src.company.router import router as company_router
from src.student.router import router as student_router
from src.utils.db import Base, engine
from src.admin.router import router as admin_router
from src.internship.router import router as internship_router
 
# The license reminder table must be imported BEFORE create_all, so that it gets created too
from src.license_expiry.model import LicenseReminderLog  # noqa: F401
from src.internship.model import InternshipModel, InternshipSkillModel  # noqa: F401
from src.utils.scheduler import start_scheduler, stop_scheduler
 
# Create all database tables (if they don't already exist)
Base.metadata.create_all(bind=engine)
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Server starts: start the daily license expiry job (runs every night at 00:00)
    start_scheduler()
    yield
    # Server stops
    stop_scheduler()
 
 
app = FastAPI(title="SmartIntern API", lifespan=lifespan)
 
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
app.include_router(admin_router)
app.include_router(internship_router)
 
 
@app.get("/")
def root():
    return {"message": "SmartIntern API is running"}
 