from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
 
from src.company.model import CompanyModel
from src.internship.controller import (
    close_internship,
    create_internship,
    delete_internship,
    get_internship,
    list_internships,
    publish_internship,
    reopen_internship,
    update_internship,
)
from src.internship.dto import (
    InternshipCreateRequest,
    InternshipListResponse,
    InternshipResponse,
    InternshipUpdateRequest,
)
from src.utils.db import get_db
from src.utils.deps import get_current_company, get_verified_company
 
router = APIRouter(prefix="/company/internships", tags=["Internships"])
 
# Reading (list / detail): any logged-in company.
# Changing (post / edit / close / reopen / publish / delete): only a VERIFIED company
#   -> pending, rejected, frozen and blocked companies get 403.
 
 
@router.post("", response_model=InternshipResponse, status_code=201)
def post_internship(
    data: InternshipCreateRequest,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    """Publish a new internship."""
    return create_internship(data, company, db)
 
 
@router.get("", response_model=InternshipListResponse)
def my_internships(
    company: CompanyModel = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """All internships of the logged-in company (newest first) with the numbers for the 4 stat cards."""
    return list_internships(company, db)
 
 
@router.get("/{internship_id}", response_model=InternshipResponse)
def internship_detail(
    internship_id: int,
    company: CompanyModel = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """One internship (used to fill the edit form)."""
    return get_internship(internship_id, company, db)
 
 
@router.put("/{internship_id}", response_model=InternshipResponse)
def edit_internship(
    internship_id: int,
    data: InternshipUpdateRequest,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    """Edit an internship. Send ALL the fields again, same rules as posting."""
    return update_internship(internship_id, data, company, db)
 
 
@router.patch("/{internship_id}/close", response_model=InternshipResponse)
def close(
    internship_id: int,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    return close_internship(internship_id, company, db)
 
 
@router.patch("/{internship_id}/reopen", response_model=InternshipResponse)
def reopen(
    internship_id: int,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    return reopen_internship(internship_id, company, db)
 
 
@router.patch("/{internship_id}/publish", response_model=InternshipResponse)
def publish(
    internship_id: int,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    """Publish a draft."""
    return publish_internship(internship_id, company, db)
 
 
@router.delete("/{internship_id}")
def delete(
    internship_id: int,
    company: CompanyModel = Depends(get_verified_company),
    db: Session = Depends(get_db),
):
    """Delete an internship (only when it has no applicants)."""
    return delete_internship(internship_id, company, db)
 