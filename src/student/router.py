from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.student.controller import create_student
from src.student.dto import StudentCreateDTO, StudentResponseDTO
from src.utils.db import get_db

# Initialize API router for student endpoints
router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "/register",
    response_model=StudentResponseDTO,
    status_code=201,
)
def register_student(body: StudentCreateDTO, db: Session = Depends(get_db)):
    """Register a new student account in the portal."""
    return create_student(body=body, db=db)