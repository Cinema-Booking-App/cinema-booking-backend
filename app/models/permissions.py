from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base

# Bảng trung gian role_permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.role_id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "permissions"
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)  # Sửa: thêm nullable=False theo schema
    module = Column(String(100), nullable=False)  # Sửa: thêm nullable=False theo schema
    actions = Column(ARRAY(String), nullable=False)  # Sửa: thêm nullable=False theo schema
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Mối quan hệ: Một quyền có thể được gán cho nhiều vai trò
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )