from datetime import datetime, timezone

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.admin.dto import AdminLoginRequest
from src.admin.model import AdminModel
from src.company.model import CompanyModel
from src.student.model import StudentModel
from src.utils.email_sender import send_company_rejected_email, send_company_verified_email
from src.utils.settings import settings
from src.utils.supabase_storage import get_signed_url

# Used to verify the admin password
password_hash = PasswordHash.recommended()

# Fields used to calculate the "profile completion" percentage of a student
PROFILE_FIELDS = [
    "phone", "university", "degree", "graduation_status", "skills",
    "location", "linkedin", "github", "portfolio", "resume_path",
]


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def utc_now() -> datetime:
    # Naive UTC time, same style as the other timestamp columns
    return datetime.now(timezone.utc).replace(tzinfo=None)


def month_start() -> datetime:
    return utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# ======================================================================
# LOGIN
# ======================================================================
def login_admin(data: AdminLoginRequest, db: Session):
    email = data.email.strip().lower()
    admin = db.query(AdminModel).filter(AdminModel.email == email).first()

    # Same message for both cases, so nobody can find out which emails exist
    if not admin or not password_hash.verify(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin email or password")

    return admin


# ======================================================================
# HELPERS: turn database rows into plain dictionaries for the frontend
# ======================================================================
def company_item(company: CompanyModel) -> dict:
    year = company.created_at.year if company.created_at else utc_now().year
    return {
        "id": company.id,
        "company_name": company.company_name,
        "email": company.email,
        "industry": company.industry,
        "contact_person": company.contact_person,
        "phone": company.phone,
        "location": company.location,
        "website": company.website,
        "description": company.description,
        "license_issue_date": company.license_issue_date,
        "license_expiry_date": company.license_expiry_date,
        "verification_status": company.verification_status,
        "rejection_reason": company.rejection_reason,
        "registration_ref": f"REG-{year}-{company.id:03d}",
        "internships_count": 0,   # will be real once the internship module exists
        "applicants_count": 0,    # will be real once the application module exists
        "created_at": company.created_at,
        "reviewed_at": company.reviewed_at,
    }


def profile_completion(student: StudentModel) -> int:
    filled = 0
    for field in PROFILE_FIELDS:
        if getattr(student, field, None):
            filled += 1
    return round(filled * 100 / len(PROFILE_FIELDS))


def student_item(student: StudentModel) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "university": student.university,
        "degree": student.degree,
        "graduation_status": student.graduation_status,
        "location": student.location,
        "skills": student.skills,
        "profile_completion": profile_completion(student),
        "applications_count": 0,  # will be real once the application module exists
        "status": "active",
        "created_at": student.created_at,
    }


def get_company_or_404(db: Session, company_id: int) -> CompanyModel:
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# ======================================================================
# DASHBOARD
# ======================================================================
def dashboard_data(db: Session):
    start = month_start()

    total_students = db.query(func.count(StudentModel.id)).scalar() or 0
    total_companies = db.query(func.count(CompanyModel.id)).scalar() or 0
    pending_companies = (
        db.query(func.count(CompanyModel.id))
        .filter(CompanyModel.verification_status == "pending")
        .scalar() or 0
    )
    new_students = (
        db.query(func.count(StudentModel.id))
        .filter(StudentModel.created_at >= start)
        .scalar() or 0
    )
    new_companies = (
        db.query(func.count(CompanyModel.id))
        .filter(CompanyModel.created_at >= start)
        .scalar() or 0
    )

    latest_pending = (
        db.query(CompanyModel)
        .filter(CompanyModel.verification_status == "pending")
        .order_by(CompanyModel.id.desc())
        .limit(3)
        .all()
    )

    return {
        "stats": {
            "students": total_students,
            "companies": total_companies,
            "pending_companies": pending_companies,
            "internships": 0,     # internship module not built yet
            "applications": 0,    # application module not built yet
            "new_students_this_month": new_students,
            "new_companies_this_month": new_companies,
        },
        "pending_companies": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "industry": c.industry,
                "created_at": c.created_at,
            }
            for c in latest_pending
        ],
    }


# ======================================================================
# STUDENTS (read only)
# ======================================================================
def list_students(db: Session):
    students = db.query(StudentModel).order_by(StudentModel.id.desc()).all()
    new_this_month = (
        db.query(func.count(StudentModel.id))
        .filter(StudentModel.created_at >= month_start())
        .scalar() or 0
    )

    return {
        "students": [student_item(s) for s in students],
        "stats": {"total": len(students), "new_this_month": new_this_month},
    }


# ======================================================================
# COMPANIES
# ======================================================================
def list_companies(db: Session, status: str = "all"):
    status = status.strip().lower()
    if status == "approved":      # the verification page calls "verified" -> "approved"
        status = "verified"
    if status not in ("all", "pending", "verified", "rejected"):
        raise bad_request("Status must be one of: all, pending, verified, rejected.")

    query = db.query(CompanyModel)
    if status != "all":
        query = query.filter(CompanyModel.verification_status == status)
    companies = query.order_by(CompanyModel.id.desc()).all()

    counts = dict(
        db.query(CompanyModel.verification_status, func.count(CompanyModel.id))
        .group_by(CompanyModel.verification_status)
        .all()
    )

    return {
        "companies": [company_item(c) for c in companies],
        "stats": {
            "total": sum(counts.values()),
            "verified": counts.get("verified", 0),
            "pending": counts.get("pending", 0),
            "rejected": counts.get("rejected", 0),
        },
    }


def get_license_link(db: Session, company_id: int):
    company = get_company_or_404(db, company_id)
    if not company.trade_license_path:
        raise HTTPException(status_code=404, detail="This company has no trade license file.")

    try:
        url = get_signed_url(settings.TRADE_LICENSE_BUCKET, company.trade_license_path, 600)
    except Exception as error:
        print(f"Could not create trade license link: {error}")
        raise HTTPException(status_code=500, detail="Could not open the trade license file.")

    if not url:
        raise HTTPException(status_code=500, detail="Could not open the trade license file.")
    if url.startswith("/"):
        url = f"{settings.SUPABASE_URL}/storage/v1{url}"

    # The link is private and works for 10 minutes only
    return {"url": url, "expires_in_seconds": 600}


def verify_company(db: Session, company_id: int):
    company = get_company_or_404(db, company_id)
    if company.verification_status == "verified":
        raise bad_request("This company is already verified.")

    company.verification_status = "verified"
    company.rejection_reason = None
    company.reviewed_at = utc_now()
    db.commit()
    db.refresh(company)

    # The status is already saved; a failed email must not undo it
    email_sent = True
    try:
        send_company_verified_email(company.email, company.company_name)
    except Exception as error:
        email_sent = False
        print(f"Could not send verification email: {error}")

    return {
        "message": "Company verified successfully.",
        "email_sent": email_sent,
        "company": company_item(company),
    }


def reject_company(db: Session, company_id: int, reason: str):
    reason = (reason or "").strip()
    if len(reason) > 500:
        raise bad_request("Reason must be 500 characters or fewer.")

    company = get_company_or_404(db, company_id)
    if company.verification_status == "rejected":
        raise bad_request("This company is already rejected.")

    company.verification_status = "rejected"
    company.rejection_reason = reason or None
    company.reviewed_at = utc_now()
    db.commit()
    db.refresh(company)

    email_sent = True
    try:
        send_company_rejected_email(company.email, company.company_name, reason)
    except Exception as error:
        email_sent = False
        print(f"Could not send rejection email: {error}")

    return {
        "message": "Company rejected.",
        "email_sent": email_sent,
        "company": company_item(company),
    }