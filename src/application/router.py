from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
 
from src.application.controller import apply_to_internship, send_applicant_notice
from src.application.dto import ApplicationResponse, ApplyRequest
from src.student.model import StudentModel
from src.utils.db import get_db
from src.utils.deps import get_current_student
 
router = APIRouter(prefix="/student/applications", tags=["Student - Applications"])
 
 
@router.post("", response_model=ApplicationResponse, status_code=201)
def apply(
    data: ApplyRequest,
    background_tasks: BackgroundTasks,
    student: StudentModel = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Apply to an internship with the details confirmed in the apply form.
    The profile resume is sent with the application. The company gets an email after the response."""
    response, notice = apply_to_internship(student, data, db)
    background_tasks.add_task(send_applicant_notice, notice)
    return response
 