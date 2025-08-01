import enum
from sqlalchemy import Column, Integer, String,  DateTime, func, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserStatusEnum(enum.Enum):
    pending = "pending" 
    active = "active"   
    inactive = "inactive"
    
class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.active, server_default='active', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Mối quan hệ: Một người dùng có nhiều vai trò
    user_roles = relationship('UserRole', backref='user', lazy=True)
    # Mối quan hệ: Một người dùng có nhiều giao dịch
    # transactions = relationship('Transaction', backref='user', lazy=True)
    # Mối quan hệ: Một người dùng có nhiều vé
    # tickets = relationship('Ticket', backref='user', lazy=True)
    # Mối quan hệ: Một người dùng có thể có nhiều đặt chỗ ghế
    # seat_reservations = relationship('SeatReservation', backref='user', lazy=True)
