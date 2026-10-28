import uuid
 
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
 
from src.application.dto import ApplyRequest
from src.application.model import ApplicationModel, ApplicationStatus
from src.application.validators import ApplicationValidationError, validate_application
from src.internship.student_controller import get_visible_internship
from src.license_expiry.config import today_local
from src.student.model import StudentModel
from src.utils.email_sender import send_new_applicant_email
from src.utils.settings import settings
from src.utils.supabase_storage import delete_file, supabase
 
 
def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)
 
 
# ======================================================================
# THE RESUME OF THE APPLICATION
# ======================================================================
def copy_profile_resume(source_path: str):
    """Copies the profile resume to a new file for this application.
    Returns (path, is_new_file). If the copy fails, the profile file itself is used (the application
    still works) and is_new_file is False."""
    extension = source_path.rsplit(".", 1)[-1] if "." in source_path else "pdf"
    new_path = f"{uuid.uuid4().hex}.{extension}"
    try:
        supabase.storage.from_(settings.RESUME_BUCKET).copy(source_path, new_path)
        return new_path, True
    except Exception as error:
        print(f"Could not copy the resume for the application: {error}")
        return source_path, False
 
 
# ======================================================================
# APPLY   (POST /student/applications)
# ======================================================================
def apply_to_internship(student: StudentModel, data: ApplyRequest, db: Session):
    """Returns (response, notice). `notice` is the data for the email to the company;
    the router sends that email AFTER the response, so the student never waits for it."""
 
    # ---------- 1. Check the details of the form (nothing is saved yet) ----------
    try:
        details = validate_application(data, today_local())
    except ApplicationValidationError as error:
        raise bad_request(str(error))
 
    # ---------- 2. The internship must be open for this student (same rules as the browse page) ----------
    internship = get_visible_internship(db, data.internship_id)
    if not internship:
        raise HTTPException(status_code=404, detail="This internship is not available for applications.")
 
    # ---------- 3. One application per internship (checked BEFORE any file is copied) ----------
    already = (
        db.query(ApplicationModel.id)
        .filter(
            ApplicationModel.student_id == student.id,
            ApplicationModel.internship_id == internship.id,
        )
        .first()
    )
    if already:
        raise bad_request("You have already applied to this internship.")
 
    # ---------- 4. The resume: a copy of the profile resume ----------
    if not student.resume_path:
        raise bad_request("Please upload your resume in your profile before applying.")
    resume_path, owns_file = copy_profile_resume(student.resume_path)
 
    # ---------- 5. Save the application ----------
    application = ApplicationModel(
        student_id=student.id,
        internship_id=internship.id,
        status=ApplicationStatus.APPLIED,
        resume_path=resume_path,
        **details,
    )
 
    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except IntegrityError:
        # Two clicks at the same moment: the unique rule stopped the second one
        db.rollback()
        if owns_file:
            delete_file(settings.RESUME_BUCKET, resume_path)
        raise bad_request("You have already applied to this internship.")
    except Exception as error:
        db.rollback()
        if owns_file:
            delete_file(settings.RESUME_BUCKET, resume_path)
        print(f"Application error: {error}")
        raise HTTPException(status_code=500, detail="Could not submit your application. Please try again.")
 
    response = {
        "id": application.id,
        "internship_id": internship.id,
        "internship_title": internship.title,
        "company_name": internship.company.company_name,
        "status": application.status,
        "applied_at": application.applied_at,
    }
    notice = {
        "to_email": internship.company.email,
        "company_name": internship.company.company_name,
        "student_name": details["full_name"],
        "university": details["university"],
        "internship_title": internship.title,
    }
    return response, notice
 
 
def send_applicant_notice(notice: dict):
    """Email to the company: 'a new applicant'. Runs in the background after the response.
    If the email fails, the application stays saved."""
    try:
        send_new_applicant_email(
            notice["to_email"],
            notice["company_name"],
            notice["student_name"],
            notice["internship_title"],
            notice.get("university"),
        )
    except Exception as error:
        print(f"Could not send the new applicant email: {error}")
 