import re
from datetime import date, datetime
 
from fastapi import HTTPException, UploadFile
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
 
from src.company.dto import CompanyLoginRequest, CompanySignupRequest
from src.company.model import CompanyModel, CompanyStatus
from src.license_expiry.config import GRACE_PERIOD_DAYS, RENEWAL_WINDOW_DAYS, today_local
from src.utils.email_sender import send_reset_email
from src.utils.password_reset import create_reset_token
from src.utils.settings import settings
from src.utils.supabase_storage import delete_file, upload_trade_license
 
# Used to securely hash and verify passwords
password_hash = PasswordHash.recommended()
 
EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
PHONE_PATTERN = r"^\+?[0-9\s\-]{7,20}$"
 
 
def bad_request(message: str) -> HTTPException:
    # Every validation problem is returned as {"detail": "message"}
    return HTTPException(status_code=400, detail=message)
 
 
def parse_date(text: str, label: str) -> date:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise bad_request(f"{label} is not valid.")
 
 
def validate_license_dates(issue_text: str, expiry_text: str):
    """Shared by signup and re-upload, so the date rules are written only once."""
    if not issue_text:
        raise bad_request("Please select the license issue date.")
    if not expiry_text:
        raise bad_request("Please select the license expiry date.")
 
    issue_date = parse_date(issue_text, "License issue date")
    expiry_date = parse_date(expiry_text, "License expiry date")
    today = today_local()
 
    if issue_date > today:
        raise bad_request("License issue date cannot be in the future.")
    if expiry_date <= issue_date:
        raise bad_request("Expiry date must be after the issue date.")
    if expiry_date < today:
        raise bad_request("Your trade license has expired.")
 
    return issue_date, expiry_date
 
 
def register_company(data: CompanySignupRequest, trade_license: UploadFile, db: Session):
    # ---------- 1. Clean the values (remove extra spaces) ----------
    company_name = data.company_name.strip()
    email = data.email.strip().lower()
    industry = data.industry.strip()
    contact_person = data.contact_person.strip()
    phone = data.phone.strip()
    location = data.location.strip()
    website = data.website.strip()
    description = data.description.strip()
    issue_text = data.license_issue_date.strip()
    expiry_text = data.license_expiry_date.strip()
 
    # ---------- 2. Check the rules ----------
    if len(company_name) < 2:
        raise bad_request("Please enter your company name.")
    if not re.match(EMAIL_PATTERN, email):
        raise bad_request("Please enter a valid email address.")
    if len(data.password) < 6:
        raise bad_request("Password must be at least 6 characters long.")
    if not industry:
        raise bad_request("Please select your industry.")
    if not contact_person:
        raise bad_request("Please enter the contact person's name.")
    if not re.match(PHONE_PATTERN, phone):
        raise bad_request("Please enter a valid contact number.")
    if not location:
        raise bad_request("Please enter the company location.")
    if website and not website.lower().startswith(("http://", "https://")):
        raise bad_request("Website must start with http:// or https://")
 
    # The trade license (file and both dates) is mandatory
    if trade_license is None or not getattr(trade_license, "filename", None):
        raise bad_request("Please upload your trade license document.")
 
    issue_date, expiry_date = validate_license_dates(issue_text, expiry_text)
 
    # ---------- 3. Email must be new (checked BEFORE uploading the file) ----------
    if db.query(CompanyModel).filter(CompanyModel.email == email).first():
        raise bad_request("Email already registered.")
 
    # ---------- 4. Upload the trade license, then save the company ----------
    license_path = upload_trade_license(trade_license)
 
    company = CompanyModel(
        company_name=company_name,
        email=email,
        password_hash=password_hash.hash(data.password),
        industry=industry,
        contact_person=contact_person,
        phone=phone,
        location=location,
        website=website or None,
        description=description or None,
        trade_license_path=license_path,
        license_issue_date=issue_date,
        license_expiry_date=expiry_date,
        verification_status=CompanyStatus.PENDING,  # admin must verify before posting
    )
 
    try:
        db.add(company)
        db.commit()
        db.refresh(company)
    except IntegrityError:
        db.rollback()
        delete_file(settings.TRADE_LICENSE_BUCKET, license_path)
        raise bad_request("Email already registered.")
    except Exception as error:
        db.rollback()
        delete_file(settings.TRADE_LICENSE_BUCKET, license_path)  # remove the uploaded file again
        print(f"Company signup error: {error}")
        raise HTTPException(status_code=500, detail="Could not create the account. Please try again.")
 
    return company
 
 
def login_company(data: CompanyLoginRequest, db: Session):
    email = data.email.strip().lower()
    company = db.query(CompanyModel).filter(CompanyModel.email == email).first()
 
    # Same message for both cases, so nobody can find out which emails exist
    if not company or not password_hash.verify(data.password, company.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
 
    # Checked only AFTER the password is correct (so emails are not revealed).
    # Blocked companies cannot enter. Pending / rejected companies
    # can login, so they can see their status and upload the license again.
    if company.verification_status == CompanyStatus.BLOCKED:
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Please contact the administrator.",
        )
 
    return company
 
 
def request_company_password_reset(email: str, db: Session):
    email = email.strip().lower()
    company = db.query(CompanyModel).filter(CompanyModel.email == email).first()
 
    # Supervisor's instruction: tell the user clearly if the email is not registered
    if not company:
        raise bad_request("This email is not registered.")
 
    token = create_reset_token(company.email, "company")
    reset_link = f"{settings.FRONTEND_RESET_URL}?token={token}"
    try:
        send_reset_email(company.email, reset_link)
    except Exception as error:
        print(f"Could not send reset email: {error}")
 
    return {"message": "A password reset link has been sent to your email."}
 
 
# =====================================================================
#  ADMIN VERIFICATION FLOW - company side
# =====================================================================
def reupload_trade_license(
    company: CompanyModel,
    trade_license: UploadFile,
    issue_text: str,
    expiry_text: str,
    db: Session,
):
    """Company uploads a new trade license: after the admin asked for it, after a rejection,
    when the account is frozen, or when its verified license is about to expire / has expired."""
    # strip + lower: a status typed by hand in the database ("Frozen", "frozen ") still works
    status = (company.verification_status or "").strip().lower()
 
    can_upload = status in (CompanyStatus.PENDING, CompanyStatus.REJECTED, CompanyStatus.FROZEN)
    if status == CompanyStatus.VERIFIED:
        days_left = company.license_days_left
        can_upload = days_left is not None and days_left <= RENEWAL_WINDOW_DAYS
    if not can_upload:
        raise bad_request(
            "You can upload a new trade license only when it is about to expire "
            f"(within {RENEWAL_WINDOW_DAYS} days), has expired, or the admin asked for it. "
            f"(Your current status: '{company.verification_status}')"
        )
 
    if trade_license is None or not getattr(trade_license, "filename", None):
        raise bad_request("Please upload your trade license document.")
 
    issue_date, expiry_date = validate_license_dates(issue_text.strip(), expiry_text.strip())
 
    # A renewal must really extend the license
    old_expiry = company.license_expiry_date
    if status == CompanyStatus.VERIFIED and old_expiry and expiry_date <= old_expiry:
        raise bad_request("The new license must expire after your current license.")
 
    old_path = company.trade_license_path
    new_path = upload_trade_license(trade_license)
 
    try:
        company.trade_license_path = new_path
        company.license_issue_date = issue_date
        company.license_expiry_date = expiry_date
        company.verification_status = CompanyStatus.PENDING  # admin must verify the new license
        company.rejection_reason = None
        company.reviewed_at = None
        db.commit()
        db.refresh(company)
    except Exception as error:
        db.rollback()
        delete_file(settings.TRADE_LICENSE_BUCKET, new_path)  # remove the new file again
        print(f"Trade license re-upload error: {error}")
        raise HTTPException(status_code=500, detail="Could not upload the license. Please try again.")
 
    # The old file is deleted only AFTER the database is saved successfully
    if old_path:
        try:
            delete_file(settings.TRADE_LICENSE_BUCKET, old_path)
        except Exception as error:
            print(f"Could not delete the old license file: {error}")
 
    return company
 
 
def ensure_company_can_post(company: CompanyModel):
    """Call this before a company creates/edits an internship (or sees candidates). Raises 403 if not allowed.
 
    Rules:
      - only a verified company can post
      - after the license expires there is a grace period (28 days) in which posting still works
      - frozen (grace period over) companies cannot post until a new license is verified
    """
    status = company.verification_status
 
    if status == CompanyStatus.BLOCKED:
        raise HTTPException(status_code=403, detail="Your account has been blocked.")
    if status == CompanyStatus.FROZEN:
        raise HTTPException(
            status_code=403,
            detail="Your account is frozen because your trade license expired. Upload a valid license to restore access.",
        )
    if status == CompanyStatus.REJECTED:
        raise HTTPException(
            status_code=403,
            detail="Your company was rejected. Please upload a corrected trade license.",
        )
    if status != CompanyStatus.VERIFIED:
        raise HTTPException(
            status_code=403,
            detail="Your company is waiting for admin verification. You can post internships once it is verified.",
        )
 
    # Extra safety: if the daily job did not run, a license that is more than 28 days expired still cannot post.
    days_left = company.license_days_left
    if days_left is not None and days_left <= -GRACE_PERIOD_DAYS:
        raise HTTPException(
            status_code=403,
            detail="Your account is frozen because your trade license expired. Upload a valid license to restore access.",
        )
 
    return company
 
 