import re
from datetime import date, datetime

from fastapi import HTTPException, UploadFile
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.company.dto import CompanyLoginRequest, CompanySignupRequest
from src.company.model import CompanyModel
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
    if not issue_text:
        raise bad_request("Please select the license issue date.")
    if not expiry_text:
        raise bad_request("Please select the license expiry date.")

    issue_date = parse_date(issue_text, "License issue date")
    expiry_date = parse_date(expiry_text, "License expiry date")
    today = date.today()

    if issue_date > today:
        raise bad_request("License issue date cannot be in the future.")
    if expiry_date <= issue_date:
        raise bad_request("Expiry date must be after the issue date.")
    if expiry_date < today:
        raise bad_request("Your trade license has expired.")

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

    return company


def request_company_password_reset(email: str, db: Session):
    email = email.strip().lower()
    company = db.query(CompanyModel).filter(CompanyModel.email == email).first()

    if company:
        token = create_reset_token(company.email, "company")
        reset_link = f"{settings.FRONTEND_RESET_URL}?token={token}"
        try:
            send_reset_email(company.email, reset_link)
        except Exception as error:
            print(f"Could not send reset email: {error}")

    return {"message": "If this email is registered, a password reset link has been sent."}