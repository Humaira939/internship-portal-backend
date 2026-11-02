from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
 
from src.contact.controller import send_contact_notice, submit_contact
from src.contact.dto import ContactRequest, ContactResponse
from src.utils.db import get_db
 
router = APIRouter(tags=["Contact"])
 
 
@router.post("/contact", response_model=ContactResponse, status_code=201)
def contact(
    data: ContactRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """The Contact Us form of the landing page. Public (no login). The message is saved and the team gets an email."""
    client_ip = request.client.host if request.client else None
    response, notice = submit_contact(data, client_ip, db)
    background_tasks.add_task(send_contact_notice, notice)
    return response
 