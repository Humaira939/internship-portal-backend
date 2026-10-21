"""Daily license expiry check: reminder emails + account freeze.
 
run_license_expiry_check() is one plain function. It is called by:
  - the APScheduler job every night at 00:00 (utils/scheduler.py)
  - once when the server starts (catch-up after downtime)
  - the command line script (scripts/run_license_check.py) for testing and the demo
"""
from datetime import date
from typing import Optional
 
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
 
from src.company.model import CompanyModel, CompanyStatus
from src.license_expiry.config import (
    D_MINUS_3,
    D_MINUS_7,
    D_ZERO,
    FROZEN,
    GRACE_PERIOD_DAYS,
    PLUS_14,
    PLUS_25,
    today_local,
)
from src.license_expiry.model import LicenseReminderLog
from src.utils.db import get_db
from src.utils.email_sender import send_license_milestone_email
 
 
# ======================================================================
# 1. Which milestone applies?
# ======================================================================
def pick_milestone(days_left: int) -> Optional[str]:
    """Returns the MOST ADVANCED milestone already reached (or None).
 
    "Reached", not "exact day": if the server was down on the exact day, the next run still finds
    the milestone. Only the latest one is returned, so a company never gets several old emails at once.
    """
    if days_left <= -GRACE_PERIOD_DAYS:
        return FROZEN
    if days_left <= -25:
        return PLUS_25
    if days_left <= -14:
        return PLUS_14
    if days_left <= 0:
        return D_ZERO
    if days_left <= 3:
        return D_MINUS_3
    if days_left <= 7:
        return D_MINUS_7
    return None
 
 
# ======================================================================
# 2. Reminder log helpers (this is what makes the job idempotent)
# ======================================================================
def _log_exists(db: Session, company_id: int, expiry: date, milestone: str) -> bool:
    return (
        db.query(LicenseReminderLog.id)
        .filter(
            LicenseReminderLog.company_id == company_id,
            LicenseReminderLog.license_expiry_date == expiry,
            LicenseReminderLog.milestone == milestone,
        )
        .first()
        is not None
    )
 
 
def _reserve(db: Session, company_id: int, expiry: date, milestone: str) -> bool:
    """Writes the log row BEFORE sending. If the row already exists, the unique constraint refuses it
    and we know the email was already sent (or another run is sending it right now)."""
    try:
        db.add(LicenseReminderLog(company_id=company_id, license_expiry_date=expiry, milestone=milestone))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
 
 
def _release(db: Session, company_id: int, expiry: date, milestone: str):
    """The email failed, so remove the log row. The next run will try again."""
    db.query(LicenseReminderLog).filter(
        LicenseReminderLog.company_id == company_id,
        LicenseReminderLog.license_expiry_date == expiry,
        LicenseReminderLog.milestone == milestone,
    ).delete()
    db.commit()
 
 
# ======================================================================
# 3. Send one milestone email
# ======================================================================
def _send_milestone(db, company, milestone, days_left, dry_run, summary):
    expiry = company.license_expiry_date
    detail = {
        "company_id": company.id,
        "email": company.email,
        "expiry_date": expiry.isoformat(),
        "days_left": days_left,
        "milestone": milestone,
    }
 
    if _log_exists(db, company.id, expiry, milestone):
        summary["skipped"] += 1
        detail["action"] = "skipped (already sent)"
        summary["details"].append(detail)
        return
 
    if dry_run:
        detail["action"] = "would send"
        summary["details"].append(detail)
        return
 
    if not _reserve(db, company.id, expiry, milestone):
        summary["skipped"] += 1
        detail["action"] = "skipped (already sent)"
        summary["details"].append(detail)
        return
 
    try:
        send_license_milestone_email(company.email, company.company_name, milestone, expiry, days_left)
    except Exception as error:
        # One bad address must not stop the whole job; the log row is removed so we retry next run
        _release(db, company.id, expiry, milestone)
        summary["failed"] += 1
        detail["action"] = f"email failed: {error}"
        print(f"License reminder email failed for company {company.id}: {error}")
    else:
        summary["sent"] += 1
        detail["action"] = "email sent"
 
    summary["details"].append(detail)
 
 
# ======================================================================
# 4. The daily job
# ======================================================================
def run_license_expiry_check(
    today: Optional[date] = None,
    company_id: Optional[int] = None,
    dry_run: bool = False,
    db: Optional[Session] = None,
) -> dict:
    """today      : pretend that this is today's date (used by the demo script)
    company_id : check only this company (used by the demo script)
    dry_run    : only report what would happen; nothing is sent or changed
    """
    today = today or today_local()
 
    owns_session = db is None
    generator = None
    if owns_session:
        generator = get_db()
        db = next(generator)
 
    summary = {
        "date": today.isoformat(),
        "checked": 0,
        "sent": 0,
        "skipped": 0,
        "failed": 0,
        "frozen": 0,
        "details": [],
    }
 
    try:
        # ---- a) Verified companies with an expiry date (verified = active; grace is computed from dates) ----
        query = db.query(CompanyModel).filter(
            CompanyModel.verification_status == CompanyStatus.VERIFIED,
            CompanyModel.license_expiry_date.isnot(None),
        )
        if company_id is not None:
            query = query.filter(CompanyModel.id == company_id)
 
        for company in query.order_by(CompanyModel.id).all():
            summary["checked"] += 1
            try:
                days_left = (company.license_expiry_date - today).days
                milestone = pick_milestone(days_left)
                if milestone is None:
                    continue
 
                if milestone == FROZEN:
                    # The freeze itself is saved first: it must not depend on the email
                    if not dry_run:
                        company.verification_status = CompanyStatus.FROZEN
                        db.commit()
                    summary["frozen"] += 1
 
                _send_milestone(db, company, milestone, days_left, dry_run, summary)
            except Exception as error:
                # Anything unexpected for ONE company must not stop the others
                db.rollback()
                summary["failed"] += 1
                print(f"License check failed for company {company.id}: {error}")
 
        # ---- b) Frozen companies whose freeze email never went out (retry) ----
        frozen_query = db.query(CompanyModel).filter(
            CompanyModel.verification_status == CompanyStatus.FROZEN,
            CompanyModel.license_expiry_date.isnot(None),
        )
        if company_id is not None:
            frozen_query = frozen_query.filter(CompanyModel.id == company_id)
 
        for company in frozen_query.order_by(CompanyModel.id).all():
            days_left = (company.license_expiry_date - today).days
            if days_left > -GRACE_PERIOD_DAYS:
                continue
            if _log_exists(db, company.id, company.license_expiry_date, FROZEN):
                continue
            try:
                _send_milestone(db, company, FROZEN, days_left, dry_run, summary)
            except Exception as error:
                db.rollback()
                summary["failed"] += 1
                print(f"Freeze email retry failed for company {company.id}: {error}")
    finally:
        if generator is not None:
            generator.close()
 
    return summary
 