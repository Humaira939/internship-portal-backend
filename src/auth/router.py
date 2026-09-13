from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from src.auth.controller import authenticate_user
from src.auth.dto import LoginDTO, TokenResponseDTO
from src.utils.db import get_db



auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login",
                  response_model=TokenResponseDTO,
                  status_code=status.HTTP_200_OK,
                  summary="Unified login endpoint for Students and Companies")
def login_user(login_data: LoginDTO, db:Session = Depends(get_db)):
    """Authenticates a student or company user and returns a Bearer access token."""
    return authenticate_user(db=db , login_data=login_data)