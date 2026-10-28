from datetime import datetime, timezone
 
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
 
from src.application.model import ApplicationModel
from src.company.model import CompanyModel
from src.internship.dto import InternshipCreateRequest, InternshipUpdateRequest
from src.internship.model import InternshipModel, InternshipSkillModel, InternshipStatus
from src.internship.validators import InternshipValidationError, validate_and_clean
from src.license_expiry.config import today_local
 
 
def bad_request(message: str) -> HTTPException:
    # Every validation problem is returned as {"detail": "message"}
    return HTTPException(status_code=400, detail=message)
 
 
def utc_now() -> datetime:
    return datetime.now(timezone.utc)
 
 
# ======================================================================
# HELPERS
# ======================================================================
def get_owned_internship(db: Session, company: CompanyModel, internship_id: int) -> InternshipModel:
    """A company can only reach its OWN internships. Someone else's id gives 404 (not 403),
    so nobody can find out which ids exist."""
    internship = (
        db.query(InternshipModel)
        .filter(InternshipModel.id == internship_id, InternshipModel.company_id == company.id)
        .first()
    )
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship
 
 
def count_applicants(db: Session, internship_id: int) -> int:
    return (
        db.query(func.count(ApplicationModel.id))
        .filter(ApplicationModel.internship_id == internship_id)
        .scalar()
        or 0
    )
 
 
def applicant_counts(db: Session, internship_ids) -> dict:
    """{internship_id: number of applications} for many internships in ONE query."""
    if not internship_ids:
        return {}
    rows = (
        db.query(ApplicationModel.internship_id, func.count(ApplicationModel.id))
        .filter(ApplicationModel.internship_id.in_(list(internship_ids)))
        .group_by(ApplicationModel.internship_id)
        .all()
    )
    return dict(rows)
 
 
def is_duplicate(db, company_id, title, start_date, exclude_id=None) -> bool:
    """Same company + same title + same start date, and not closed = an accidental double post."""
    query = db.query(InternshipModel.id).filter(
        InternshipModel.company_id == company_id,
        func.lower(InternshipModel.title) == title.lower(),
        InternshipModel.start_date == start_date,
        InternshipModel.status != InternshipStatus.CLOSED,
    )
    if exclude_id is not None:
        query = query.filter(InternshipModel.id != exclude_id)
    return query.first() is not None
 
 
def save(db: Session, internship: InternshipModel, error_message: str):
    try:
        internship.updated_at = utc_now()
        db.commit()
        db.refresh(internship)
    except Exception as error:
        db.rollback()
        print(f"Internship save error: {error}")
        raise HTTPException(status_code=500, detail=error_message)
    internship.applicants_count = count_applicants(db, internship.id)
    return internship
 
 
# ======================================================================
# CREATE  (POST /company/internships)
# ======================================================================
def create_internship(data: InternshipCreateRequest, company: CompanyModel, db: Session):
    """The company must already be verified: the router checks it with get_verified_company."""
 
    # ---------- 1. Check and clean every field ----------
    try:
        values = validate_and_clean(data, today_local())
    except InternshipValidationError as error:
        raise bad_request(str(error))
 
    skills = values.pop("skills")
 
    # ---------- 2. Stop an accidental double post (same title + same start date, still open) ----------
    if is_duplicate(db, company.id, values["title"], values["start_date"]):
        raise bad_request("You have already posted an internship with the same title and start date.")
 
    # ---------- 3. Save the internship together with its skills ----------
    internship = InternshipModel(
        company_id=company.id,
        status=InternshipStatus.ACTIVE,    # the form has only "Publish", so it is published at once
        **values,
    )
    internship.skills = [
        InternshipSkillModel(skill_name=name, skill_key=key) for name, key in skills
    ]
 
    try:
        db.add(internship)
        db.commit()
        db.refresh(internship)
    except Exception as error:
        db.rollback()
        print(f"Create internship error: {error}")
        raise HTTPException(status_code=500, detail="Could not publish the internship. Please try again.")
 
    return internship
 
 
# ======================================================================
# LIST  (GET /company/internships)  - search, filter and sort are done by the frontend
# ======================================================================
def list_internships(company: CompanyModel, db: Session):
    internships = (
        db.query(InternshipModel)
        .options(selectinload(InternshipModel.skills))      # loads all skills in one query
        .filter(InternshipModel.company_id == company.id)
        .order_by(InternshipModel.created_at.desc(), InternshipModel.id.desc())
        .all()
    )
 
    counts = applicant_counts(db, [item.id for item in internships])
    for item in internships:
        item.applicants_count = counts.get(item.id, 0)      # shown on each card
 
    applicants = sum(counts.values())
    stats = {
        "total": len(internships),
        "active": sum(1 for item in internships if item.status == InternshipStatus.ACTIVE),
        "draft": sum(1 for item in internships if item.status == InternshipStatus.DRAFT),
        "closed": sum(1 for item in internships if item.status == InternshipStatus.CLOSED),
        "applicants": applicants,
    }
    return {"internships": internships, "stats": stats}
 
 
# ======================================================================
# ONE INTERNSHIP  (GET /company/internships/{id})
# ======================================================================
def get_internship(internship_id: int, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
    internship.applicants_count = count_applicants(db, internship.id)
    return internship
 
 
# ======================================================================
# EDIT  (PUT /company/internships/{id})
# ======================================================================
def update_internship(internship_id: int, data: InternshipUpdateRequest, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
 
    if internship.status == InternshipStatus.CLOSED:
        raise bad_request("This internship is closed. Reopen it before editing.")
 
    # The same rules as posting. A date that is already in the past is accepted only if it is unchanged.
    try:
        values = validate_and_clean(
            data,
            today_local(),
            existing_start=internship.start_date,
            existing_deadline=internship.application_deadline,
        )
    except InternshipValidationError as error:
        raise bad_request(str(error))
 
    skills = values.pop("skills")
 
    if is_duplicate(db, company.id, values["title"], values["start_date"], exclude_id=internship.id):
        raise bad_request("You already have another internship with the same title and start date.")
 
    for field, value in values.items():
        setattr(internship, field, value)
 
    # Skills: keep the ones that stay, remove the ones that are gone, add the new ones.
    # (Replacing all rows at once would break the unique rule when the same skill stays.)
    existing = {row.skill_key: row for row in internship.skills}
    new_keys = {key for _, key in skills}
 
    for key, row in existing.items():
        if key not in new_keys:
            internship.skills.remove(row)
 
    for name, key in skills:
        if key in existing:
            existing[key].skill_name = name
        else:
            internship.skills.append(InternshipSkillModel(skill_name=name, skill_key=key))
 
    return save(db, internship, "Could not save the changes. Please try again.")
 
 
# ======================================================================
# CLOSE / REOPEN / PUBLISH  (PATCH /company/internships/{id}/close | reopen | publish)
# ======================================================================
def close_internship(internship_id: int, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
    if internship.status != InternshipStatus.ACTIVE:
        raise bad_request("Only an active internship can be closed.")
 
    internship.status = InternshipStatus.CLOSED
    internship.closed_at = utc_now()
    return save(db, internship, "Could not close the internship. Please try again.")
 
 
def reopen_internship(internship_id: int, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
    if internship.status != InternshipStatus.CLOSED:
        raise bad_request("Only a closed internship can be reopened.")
 
    # If its deadline is already over, the response has deadline_passed = true and students do not see it
    # until the company edits the deadline.
    internship.status = InternshipStatus.ACTIVE
    internship.closed_at = None
    return save(db, internship, "Could not reopen the internship. Please try again.")
 
 
def publish_internship(internship_id: int, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
    if internship.status != InternshipStatus.DRAFT:
        raise bad_request("Only a draft can be published.")
 
    internship.status = InternshipStatus.ACTIVE
    return save(db, internship, "Could not publish the internship. Please try again.")
 
 
# ======================================================================
# DELETE  (DELETE /company/internships/{id})
# ======================================================================
def delete_internship(internship_id: int, company: CompanyModel, db: Session):
    internship = get_owned_internship(db, company, internship_id)
 
    # With applicants the internship must be closed, not deleted (their applications would be lost)
    if count_applicants(db, internship.id) > 0:
        raise bad_request("This internship has applicants, so it cannot be deleted. Close it instead.")
 
    try:
        db.delete(internship)          # its skills are deleted with it
        db.commit()
    except Exception as error:
        db.rollback()
        print(f"Delete internship error: {error}")
        raise HTTPException(status_code=500, detail="Could not delete the internship. Please try again.")
 
    return {"message": "Internship deleted.", "id": internship_id}
 