import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum, Boolean, ForeignKey, Date, Numeric
from datetime import datetime                                                                                                               
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserStatusEnum(enum.Enum):
    pending = "pending" 
    active = "active"   
    inactive = "inactive"

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    
class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)                                                                                                         
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    # Thông tin cá nhân
    avatar_url = Column(String(500), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    # Trạng thái & bảo mật
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.active, server_default='active', nullable=False)
    is_verified = Column(Boolean, default=False, server_default="false")
    last_login = Column(DateTime, nullable=True)
    # Quản lý khách hàng
    loyalty_points = Column(Integer, default=0, server_default="0")
    rank_id = Column(Integer, ForeignKey("ranks.rank_id"), nullable=True)
    total_spent = Column(Numeric(15,2), default=0, server_default="0")  # Thêm cột total_spent
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Mối quan hệ: Một người dùng có nhiều giao dịch
    transactions = relationship("Transaction",back_populates="user",foreign_keys="[Transaction.user_id]")
    # Mối quan hệ: Một người dùng có nhiều vé
    tickets = relationship("Tickets", back_populates="user", lazy=True) 
    # Một rank có nhiều user
    rank = relationship("Ranks", back_populates="users")  
    # Mối quan hệ: Một người dùng có thể có nhiều đặt chỗ ghế
    # seat_reservations = relationship('SeatReservation', backref='user', lazy=True)

    roles = relationship("Role", secondary="user_roles", back_populates="users")