from math import ceil
from typing import Optional
 
from fastapi import HTTPException
from sqlalchemy import and_, exists, func, or_
from sqlalchemy.orm import Session, contains_eager, selectinload
 
from src.application.model import ApplicationModel
from src.company.model import CompanyModel, CompanyStatus
from src.internship.model import InternshipModel, InternshipSkillModel, InternshipStatus
from src.internship.student_helpers import (
    FilterError,
    like_pattern,
    parse_category,
    parse_duration,
    parse_location,
    parse_type,
    search_words,
    to_card,
    to_detail,
)
from src.license_expiry.config import today_local
from src.student.model import StudentModel
 
ESCAPE = "\\"
 
 
def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)
 
 
def visible_conditions():
    """WHICH internships a student may see:
       - the internship is active (not closed / not a draft)
       - its application deadline is not over (the deadline day itself is still open)
       - its company is verified (blocked, frozen, pending, rejected companies are hidden)"""
    today = today_local()
    return [
        InternshipModel.status == InternshipStatus.ACTIVE,
        or_(
            InternshipModel.application_deadline.is_(None),
            InternshipModel.application_deadline >= today,
        ),
        CompanyModel.verification_status == CompanyStatus.VERIFIED,
    ]
 
 
def applied_internship_ids(db: Session, student: StudentModel, internship_ids) -> set:
    """Of these internships, the ids this student has already applied to."""
    if not internship_ids:
        return set()
    rows = (
        db.query(ApplicationModel.internship_id)
        .filter(
            ApplicationModel.student_id == student.id,
            ApplicationModel.internship_id.in_(list(internship_ids)),
        )
        .all()
    )
    return {row[0] for row in rows}
 
 
def get_visible_internship(db: Session, internship_id: int):
    """One internship, only if the student is allowed to see it (open, deadline not over, verified company)."""
    return (
        db.query(InternshipModel)
        .join(InternshipModel.company)
        .options(contains_eager(InternshipModel.company), selectinload(InternshipModel.skills))
        .filter(InternshipModel.id == internship_id, *visible_conditions())
        .first()
    )
 
 
# ======================================================================
# BROWSE  (GET /student/internships)
# ======================================================================
def browse_internships(
    student: StudentModel,
    db: Session,
    q: Optional[str],
    type_: Optional[str],
    location: Optional[str],
    duration: Optional[str],
    category: Optional[str],
    page: int,
    page_size: int,
):
    # ---------- 1. Read the filters ----------
    try:
        arrangement = parse_type(type_)
        months = parse_duration(duration)
    except FilterError as error:
        raise bad_request(str(error))
    place = parse_location(location)
    category = parse_category(category)
    words = search_words(q)
 
    # ---------- 2. Build the query: visible internships + the student's search and filters ----------
    conditions = visible_conditions()
 
    if arrangement:
        conditions.append(InternshipModel.work_arrangement == arrangement)
 
    if place == "remote":
        conditions.append(InternshipModel.work_arrangement == "Remote")
    elif place:
        conditions.append(InternshipModel.office_city.ilike(like_pattern(place), escape=ESCAPE))
 
    if months:
        conditions.append(InternshipModel.duration.ilike(f"{months} month%"))
 
    if category:
        conditions.append(func.lower(InternshipModel.category).in_([name.lower() for name in category]))
 
    # Every word of the search must be found in the title, category, company name or one of the skills
    for word in words:
        pattern = like_pattern(word)
        skill_match = exists().where(
            and_(
                InternshipSkillModel.internship_id == InternshipModel.id,
                InternshipSkillModel.skill_name.ilike(pattern, escape=ESCAPE),
            )
        )
        conditions.append(
            or_(
                InternshipModel.title.ilike(pattern, escape=ESCAPE),
                InternshipModel.category.ilike(pattern, escape=ESCAPE),
                CompanyModel.company_name.ilike(pattern, escape=ESCAPE),
                skill_match,
            )
        )
 
    # ---------- 3. Count all matches, then take only the requested page ----------
    total = (
        db.query(func.count(InternshipModel.id))
        .join(CompanyModel, InternshipModel.company_id == CompanyModel.id)
        .filter(*conditions)
        .scalar()
        or 0
    )
 
    internships = (
        db.query(InternshipModel)
        .join(InternshipModel.company)
        .options(contains_eager(InternshipModel.company), selectinload(InternshipModel.skills))
        .filter(*conditions)
        .order_by(InternshipModel.created_at.desc(), InternshipModel.id.desc())   # newest first
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
 
    applied_ids = applied_internship_ids(db, student, [item.id for item in internships])
 
    return {
        "internships": [to_card(item, applied_ids) for item in internships],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total,
    }
 
 
# ======================================================================
# DETAIL  (GET /student/internships/{id})
# ======================================================================
def internship_detail(internship_id: int, student: StudentModel, db: Session):
    internship = get_visible_internship(db, internship_id)
 
    # Closed, expired, draft and hidden-company internships look exactly like a missing one
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
 
    has_applied = internship.id in applied_internship_ids(db, student, [internship.id])
    return to_detail(internship, has_applied=has_applied)
 