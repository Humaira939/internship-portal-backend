from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.controller import create_admin
from src.admin.dto import AdminSchema
from src.utils.db import get_db

router = APIRouter(prefix="/admin", tags=["Admin Module"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
def add_admin(data: AdminSchema, db: Session = Depends(get_db)):
    admin = create_admin(data=data, db=db)
    if not admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    return {
        "message": "Admin created successfully",
        "username": admin.username,
    }