from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.models.user import User, UserStatusEnum ,UserRoleEnum
from app.schemas.user import UserLogin, UserRegister, UserResponse
from app.services.user_service import pwd_context


def register(db: Session, user_in : UserRegister):
    try:
        # Kiểm tra xem email đã tồn tại chưa
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        
        hashed_password = pwd_context.hash(user_in.password)
        user = User(
            full_name=user_in.full_name,
            email=user_in.email,
            phone_number=user_in.phone_number,
            password_hash=hashed_password,
            status= UserStatusEnum.active,
            role = UserRoleEnum.customer,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Lỗi dữ liệu: {str(e)}"
        ) 
def login(db: Session, user_in: UserLogin):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not pwd_context.verify(user_in.password, getattr(user, "password_hash", None)):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token({"sub": user.email, "role": str(user.role)})
    refresh_token = create_access_token({"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }