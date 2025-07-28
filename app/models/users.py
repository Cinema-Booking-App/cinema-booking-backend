import enum
from sqlalchemy import Column, Integer, String,  DateTime, func, Enum
from app.core.database import Base


class UserStatusEnum(enum.Enum):
    pending = "pending" 
    active = "active"   
    inactive = "inactive"
    
class UserRoleEnum(enum.Enum):
    admin = 'admin'
    theater_manager = 'theater_manager'
    staff = 'staff'
    customer = 'customer'

class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.active, server_default='active', nullable=False)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.customer, server_default='customer')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
