from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.users import Users
from app.schemas.users import UserResponse, UserUpdate
from passlib.context import CryptContext
from app.schemas.users import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Lấy danh sách người dùng
def get_all_users(db : Session):
       users = db.query(Users).all()
       return [UserResponse.from_orm(u) for u in users ]

# Lấy người dùng theo id
def get_user_by_id(db: Session, user_id: int):
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if user:
        return UserResponse.from_orm(user)
    return None

# Tạo người dùng mới
def create_user(db: Session, user_in: UserCreate):
    try:
        hashed_password = pwd_context.hash(user_in.password)
        user = Users(
            full_name=user_in.full_name,
            email=user_in.email,
            password_hash=hashed_password,
            status=user_in.status,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f" {str(e)}")

#Xóa người dùng theo id
def delete_user(db: Session, user_id: int):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
        db.commit()
        # trả về tin nhắn xóa thành công
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f" {str(e)}")

#Sửa người dùng theo id
def update_user(db: Session, user_id: int, user_in: UserUpdate):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Cập nhật thông tin người dùng
        updated_user = user_in.dict(exclude_unset=True)
        for key, value in updated_user.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f" {str(e)}")