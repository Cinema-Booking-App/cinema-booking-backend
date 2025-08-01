from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String,Text


class Roles(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Mối quan hệ: Một vai trò có nhiều quyền
    role_permissions = relationship("RolePermission", backref="role", lazy=True)
    # Mối quan hệ: Một vai trò có thể được gán cho nhiều người dùng
    user_roles = relationship("UserRole", backref="role", lazy=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_role_id = Column(Integer, primary_key=True)  # ID duy nhất cho mỗi dòng
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_permission_id = Column(Integer, primary_key=True)  # ID duy nhất cho mỗi dòng
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    permission_id = Column(
        Integer, ForeignKey("permissions.permission_id"), nullable=False
    )
