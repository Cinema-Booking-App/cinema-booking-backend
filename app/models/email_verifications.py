from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.core.database import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    email_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    verification_code = Column(String, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(),server_default=func.now()) 
    expires_at = Column(DateTime, nullable=False)