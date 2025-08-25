from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.users import Users, UserStatusEnum
from app.schemas.users import UserResponse, UserCreate, UserUpdate
from passlib.context import CryptContext
from app.models.ranks import Ranks  # Import mô hình Ranks

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Lấy danh sách người dùng với phân trang và tìm kiếm
def get_all_users(db: Session, skip: int = 0, limit: int = 10, search_query: str = None):
    try:
        query = db.query(Users)
        if search_query:
            query = query.filter(
                (Users.full_name.ilike(f"%{search_query}%")) |
                (Users.email.ilike(f"%{search_query}%"))
            )
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return {"items": [UserResponse.from_orm(u) for u in users], "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy danh sách người dùng: {str(e)}")

# Lấy người dùng theo id
def get_user_by_id(db: Session, user_id: int):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if user:
            return UserResponse.from_orm(user)
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy người dùng: {str(e)}")

# Lấy người dùng theo email
def get_user_by_email(db: Session, email: str):
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if user:
            return UserResponse.from_orm(user)
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy người dùng theo email: {str(e)}")

# Tạo người dùng mới
def create_user(db: Session, user_in: UserCreate):
    try:
        # Kiểm tra email đã tồn tại chưa
        if get_user_by_email(db, user_in.email):
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        
        hashed_password = pwd_context.hash(user_in.password)
        user = Users(
            full_name=user_in.full_name,
            email=user_in.email,
            password_hash=hashed_password,
            phone=user_in.phone,
            avatar_url=user_in.avatar_url,
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender,
            status=user_in.status,
            is_verified=user_in.is_verified
        )
        # Gán rank mặc định khi tạo người dùng
        default_rank = db.query(Ranks).filter(Ranks.is_default == True).first()
        if default_rank:
            user.rank_id = default_rank.rank_id
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo người dùng: {str(e)}")

# Xóa người dùng theo id
def delete_user(db: Session, user_id: int):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        db.delete(user)
        db.commit()
        return {"message": "Xóa người dùng thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa người dùng: {str(e)}")

# Sửa người dùng theo id
def update_user(db: Session, user_id: int, user_in: UserUpdate):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        # Cập nhật thông tin người dùng
        updated_user = user_in.dict(exclude_unset=True)
        for key, value in updated_user.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật người dùng: {str(e)}")

# Đặt lại mật khẩu (admin reset password)
# def reset_user_password(db: Session, user_id: int, new_password: str):
#     try:
#         user = db.query(Users).filter(Users.user_id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
#         user.password_hash = pwd_context.hash(new_password)
#         db.commit()
#         db.refresh(user)
#         return {"message": "Đặt lại mật khẩu thành công"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Lỗi khi đặt lại mật khẩu: {str(e)}")

# Cập nhật trạng thái người dùng (active/inactive/pending)
def update_user_status(db: Session, user_id: int, status: UserStatusEnum):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        user.status = status
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật trạng thái người dùng: {str(e)}")

# Lấy rank phù hợp dựa trên total_spent
def get_appropriate_rank(db: Session, total_spent: float):
    try:
# Tìm rank có spending_target nhỏ hơn hoặc bằng total_spent, sắp xếp giảm dần để lấy rank cao nhất
        rank = db.query(Ranks).filter(Ranks.spending_target <= total_spent).order_by(Ranks.spending_target.desc()).first()
        if not rank:
            # Nếu không tìm thấy rank phù hợp, trả về rank mặc định
            rank = db.query(Ranks).filter(Ranks.is_default == True).first()
            if not rank:
                raise HTTPException(status_code=404, detail="Không tìm thấy rank mặc định")
        return rank
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy rank: {str(e)}")

# Cập nhật điểm tích lũy (loyalty points)
def update_loyalty_points(db: Session, user_id: int, points: int):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        user.loyalty_points = points
        if user.loyalty_points < 0:
            user.loyalty_points = 0  # Đảm bảo điểm không âm
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật điểm tích lũy: {str(e)}")

# Cập nhật tổng chi tiêu (total_spent) và tự động cập nhật rank
def update_total_spent(db: Session, user_id: int, amount: float):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        user.total_spent = amount
        if user.total_spent < 0:
            user.total_spent = 0  # Đảm bảo tổng chi tiêu không âm
        
        # Tự động cập nhật rank dựa trên total_spent
        rank = get_appropriate_rank(db, user.total_spent)
        user.rank_id = rank.rank_id
        
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật tổng chi tiêu: {str(e)}")

# Xác thực người dùng (verify user)
def verify_user(db: Session, user_id: int):
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Người dùng đã được xác thực")
        user.is_verified = True
        user.status = UserStatusEnum.active  # Kích hoạt người dùng khi xác thực
        db.commit()
        db.refresh(user)
        return UserResponse.from_orm(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xác thực người dùng: {str(e)}")