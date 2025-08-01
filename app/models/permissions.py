from typing import Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import Column, Integer, String


class Permissions(Base):
    __tablename__ = "permissions"
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Mối quan hệ: Một quyền có thể được gán cho nhiều vai trò
    role_permissions = relationship("RolePermission", backref="permission", lazy=True)
