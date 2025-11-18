from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.permissions import Permission
from app.models.role import Role, UserRole
from app.schemas.roles import PermissionCreate, PermissionResponse, RoleCreate, RoleResponse


# Danh sách vai trò
def get_list_roles(db: Session):
    roles = (
        db.query(
            Role,
            func.count(UserRole.user_id).label("user_count"),
            func.count(Permission.permission_id).label("permission_count")
        )
        .outerjoin(UserRole, Role.role_id == UserRole.role_id)
        .outerjoin(Role.permissions)
        .group_by(Role.role_id)
        .options(joinedload(Role.permissions))
        .all()
    )
    results = []
    for role, user_count, permission_count in roles:
        # Lấy danh sách permissions đã được tải sẵn
        permissions_list = [
            PermissionResponse.model_validate(p) for p in role.permissions
        ]
        
        results.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "user_count": user_count,
            "permission_count": permission_count,
            "permissions": permissions_list
        })
    return results

def create_role_with_permissions( data: RoleCreate, db: Session):
    try:
        # Bước 1: Tạo đối tượng Role
        db_role = Role(
            role_name=data.role_name,
            description=data.description
        )

        # Bước 2: Tìm các đối tượng Permission từ các ID
        permissions_to_add = db.query(Permission).filter(
            Permission.permission_id.in_(data.permission_ids)
        ).all()
        
        # Bước 3: Gán trực tiếp danh sách các đối tượng Permission
        db_role.permissions = permissions_to_add

        db.add(db_role)
        db.commit()
        db.refresh(db_role)

        return RoleResponse.from_orm(db_role)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")

def delete_role( role_id: int,db: Session):
    try:
        role = db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        db.delete(role)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")
        

# Danh sách quyền
def get_all_permissions(db: Session):
    permissions = db.query(Permission).all()
    return [PermissionResponse.from_orm(permission) for permission in permissions]

# Tạo quyền mới
# Thêm phim mới
def create_permissions(db: Session, data: PermissionCreate):
    try:
        # Tạo đối tượng Movie từ dữ liệu đầu vào
        db_movie = Permission(**data.dict(exclude_unset=True))
        # Thêm vào session
        db.add(db_movie)
        # Lưu thay đổi vào database
        db.commit()
        # Làm mới đối tượng để lấy dữ liệu mới nhất từ DB
        db.refresh(db_movie)
        return db_movie
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")