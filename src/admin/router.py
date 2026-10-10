from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.admin.controller import (
    dashboard_data,
    get_license_link,
    list_companies,
    list_students,
    login_admin,
    reject_company,
    verify_company,
)
from src.admin.dto import AdminLoginRequest, AdminTokenResponse, RejectCompanyRequest
from src.utils.db import get_db
from src.utils.deps import get_current_admin
from src.utils.security import create_access_token

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------- Login (the only public admin route) ----------
@router.post("/login", response_model=AdminTokenResponse)
def login(data: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = login_admin(data, db)
    token = create_access_token({"sub": admin.email, "role": "admin"})
    return AdminTokenResponse(access_token=token, admin=admin)


# ---------- Everything below needs a valid admin token ----------
@router.get("/dashboard", dependencies=[Depends(get_current_admin)])
def dashboard(db: Session = Depends(get_db)):
    return dashboard_data(db)


@router.get("/students", dependencies=[Depends(get_current_admin)])
def students(db: Session = Depends(get_db)):
    return list_students(db)


@router.get("/companies", dependencies=[Depends(get_current_admin)])
def companies(status: str = "all", db: Session = Depends(get_db)):
    return list_companies(db, status)


@router.get("/companies/{company_id}/license", dependencies=[Depends(get_current_admin)])
def company_license(company_id: int, db: Session = Depends(get_db)):
    return get_license_link(db, company_id)


@router.patch("/companies/{company_id}/verify", dependencies=[Depends(get_current_admin)])
def verify(company_id: int, db: Session = Depends(get_db)):
    return verify_company(db, company_id)


@router.patch("/companies/{company_id}/reject", dependencies=[Depends(get_current_admin)])
def reject(
    company_id: int,
    data: Optional[RejectCompanyRequest] = None,
    db: Session = Depends(get_db),
):
    reason = data.reason if data else ""
    return reject_company(db, company_id, reason)