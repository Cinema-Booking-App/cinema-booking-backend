from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserResponse
from passlib.context import CryptContext
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Lấy danh sách người dùng
def get_all_users(db : Session):
       users = db.query(User).all()
       return [UserResponse.from_orm(u) for u in users ]

# Lấy người dùng theo id
def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        return UserResponse.from_orm(user)
    return None

def create_user(db: Session, user_in: UserCreate):
    try:
        hashed_password = pwd_context.hash(user_in.password)
        user = User(
            full_name=user_in.full_name,
            email=user_in.email,
            phone_number=user_in.phone_number,
            password_hash=hashed_password,
            status=user_in.status,
            role=user_in.role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception:
        db.rollback()
        raise
