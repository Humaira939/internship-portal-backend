from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from src.company.controller import create_company
from src.company.dto import CompanyCreateDTO,CompanyResponseDTO
from src.utils.db import get_db

router = APIRouter(prefix="/companies",tags=["Companies"])

@router.post("/register",response_model=CompanyResponseDTO, status_code=201)
def register_company(body:CompanyCreateDTO,db:Session = Depends(get_db)):
    return create_company(body=body, db=db)
