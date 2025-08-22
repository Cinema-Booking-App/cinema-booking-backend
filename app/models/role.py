from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String,Text, func

from app.models.permissions import role_permissions


class Role(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(255), nullable=False)  # Sửa: thay đổi độ dài theo schema
    description = Column(String(255), unique=True, nullable=False)  # Sửa: thêm unique và nullable=False
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_roles = relationship("UserRole", back_populates="role", lazy=True)
    permissions = relationship("Permissions",secondary=role_permissions,back_populates="roles"
    )
class UserRole(Base):
    __tablename__ = "user_roles"
    user_role_id = Column(Integer, primary_key=True)  # ID duy nhất cho mỗi dòng
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    role = relationship("Role", back_populates="user_roles")
