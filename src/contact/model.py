from datetime import datetime, timezone
 
from sqlalchemy import Column, DateTime, Integer, String, Text
 
from src.utils.db import Base
 
 
def utc_now() -> datetime:
    # naive UTC time, so that comparing times ("in the last hour") always works the same way
    return datetime.now(timezone.utc).replace(tzinfo=None)
 
 
class ContactMessageStatus:
    NEW = "new"          # nobody has looked at it yet
    READ = "read"        # the admin page (later) can use these two
    REPLIED = "replied"
 
 
class ContactMessageModel(Base):
    """A message sent from the Contact Us form of the landing page (the visitor is not logged in)."""
 
    __tablename__ = "contact_messages"
 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(10), nullable=False)          # student / company / other
    topic = Column(String(20), nullable=False)         # general / account / internship / company / technical / feedback
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="new", server_default="new", index=True)
 
    # Used by the spam protection (limits per IP / per email, and the same message twice)
    ip_address = Column(String(45), nullable=True, index=True)
    message_hash = Column(String(64), nullable=False, index=True)
 
    created_at = Column(DateTime, default=utc_now, index=True)
 