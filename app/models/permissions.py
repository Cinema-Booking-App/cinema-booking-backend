from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base


class Permissions(Base):
    __tablename__ = "permissions"
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String, nullable=True)
    actions = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # Mối quan hệ: Một quyền có thể được gán cho nhiều vai trò
    role_permissions = relationship("RolePermission", backref="permission", lazy=True)
