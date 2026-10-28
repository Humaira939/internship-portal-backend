from typing import Optional
 
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
 
from src.internship.student_controller import browse_internships, internship_detail
from src.internship.student_dto import StudentInternshipDetail, StudentInternshipList
from src.student.model import StudentModel
from src.utils.db import get_db
from src.utils.deps import get_current_student
 
router = APIRouter(prefix="/student/internships", tags=["Student - Internships"])
 
 
@router.get("", response_model=StudentInternshipList)
def browse(
    q: str = Query("", max_length=100, description="search: title, skills, company, category"),
    type: str = Query("all", description="all | remote | onsite | hybrid"),
    location: str = Query("all", description="all | remote | a city name"),
    duration: str = Query("all", description="all | number of months, e.g. 3"),
    category: str = Query("all", description="all | a category, e.g. Data Science"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    student: StudentModel = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """The Browse Internships page: only open internships of verified companies."""
    return browse_internships(student, db, q, type, location, duration, category, page, page_size)
 
 
@router.get("/{internship_id}", response_model=StudentInternshipDetail)
def detail(
    internship_id: int,
    student: StudentModel = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """The Internship Details page (with the company's public information)."""
    return internship_detail(internship_id, student, db)
 