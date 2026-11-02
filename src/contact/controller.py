from datetime import timedelta
from typing import Optional
 
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
 
from src.contact.dto import ContactRequest
from src.contact.model import ContactMessageModel, ContactMessageStatus, utc_now
from src.contact.validators import ContactValidationError, validate_contact
from src.utils.email_sender import send_contact_message_email
from src.utils.settings import settings
 
# Spam protection (can be changed in utils/settings.py)
MAX_PER_IP_PER_HOUR = int(getattr(settings, "CONTACT_MAX_PER_IP_PER_HOUR", 5))
MAX_PER_EMAIL_PER_HOUR = int(getattr(settings, "CONTACT_MAX_PER_EMAIL_PER_HOUR", 3))
SAME_MESSAGE_HOURS = 24
 
 
def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)
 
 
def too_many() -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="You have sent too many messages. Please try again a little later.",
    )
 
 
def count_since(db: Session, since, **match) -> int:
    query = db.query(func.count(ContactMessageModel.id)).filter(ContactMessageModel.created_at >= since)
    for column, value in match.items():
        query = query.filter(getattr(ContactMessageModel, column) == value)
    return query.scalar() or 0
 
 
# ======================================================================
# SEND A MESSAGE   (POST /contact)
# ======================================================================
def submit_contact(data: ContactRequest, client_ip: Optional[str], db: Session):
    """Returns (response, notice). `notice` is the data of the email to the team;
    the router sends that email AFTER the response, so the visitor never waits for it."""
 
    # ---------- 1. Check every field ----------
    try:
        values = validate_contact(data)
    except ContactValidationError as error:
        raise bad_request(str(error))
 
    now = utc_now()
    hour_ago = now - timedelta(hours=1)
 
    # ---------- 2. Spam protection (this form is open to everybody) ----------
    if client_ip and count_since(db, hour_ago, ip_address=client_ip) >= MAX_PER_IP_PER_HOUR:
        raise too_many()
    if count_since(db, hour_ago, email=values["email"]) >= MAX_PER_EMAIL_PER_HOUR:
        raise too_many()
 
    same_message = (
        db.query(ContactMessageModel.id)
        .filter(
            ContactMessageModel.message_hash == values["message_hash"],
            ContactMessageModel.created_at >= now - timedelta(hours=SAME_MESSAGE_HOURS),
        )
        .first()
    )
    if same_message:
        raise bad_request("We have already received this message. We will get back to you soon.")
 
    # ---------- 3. Save it (so it is not lost even if the email fails) ----------
    row = ContactMessageModel(
        **values,
        status=ContactMessageStatus.NEW,
        ip_address=client_ip,
        created_at=now,
    )
 
    try:
        db.add(row)
        db.commit()
        db.refresh(row)
    except Exception as error:
        db.rollback()
        print(f"Contact message error: {error}")
        raise HTTPException(status_code=500, detail="Could not send your message. Please try again.")
 
    notice = {
        "to_email": getattr(settings, "SUPPORT_EMAIL", "") or settings.EMAIL_ADDRESS,
        "message_id": row.id,
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "role": row.role,
        "topic": row.topic,
        "message": row.message,
    }
    return {"message": "Thank you. Your message has been sent."}, notice
 
 
def send_contact_notice(notice: dict):
    """Email to the SmartIntern team. Runs in the background after the response.
    If the email fails, the message stays saved in the database."""
    try:
        send_contact_message_email(
            to_email=notice["to_email"],
            message_id=notice["message_id"],
            name=notice["name"],
            email=notice["email"],
            phone=notice["phone"],
            role=notice["role"],
            topic=notice["topic"],
            message=notice["message"],
        )
    except Exception as error:
        print(f"Could not send the contact message email: {error}")
 