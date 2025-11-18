"""
Module khởi tạo dữ liệu mặc định cho hệ thống
Tạo các role và user admin mặc định khi ứng dụng khởi động
"""
from sqlalchemy.orm import Session
from app.models.users import Users, UserStatusEnum
from app.models.role import Role, UserRole
from app.services.users_service import pwd_context
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def init_roles(db: Session):
    """Khởi tạo các role mặc định"""
    default_roles = [
        {
            "role_name": "super_admin",
            "description": "Quản trị viên cấp cao - toàn quyền quản lý hệ thống"
        },
        {
            "role_name": "theater_admin",
            "description": "Quản trị viên rạp - quản lý rạp chiếu phim"
        },
        {
            "role_name": "theater_manager",
            "description": "Quản lý rạp - quản lý suất chiếu và vận hành"
        },
        {
            "role_name": "user",
            "description": "Người dùng thông thường"
        }
    ]
    
    created_count = 0
    for role_data in default_roles:
        existing_role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()
        if not existing_role:
            new_role = Role(**role_data)
            db.add(new_role)
            created_count += 1
            logger.info(f"✅ Đã tạo role: {role_data['role_name']}")
        else:
            logger.info(f"ℹ️  Role đã tồn tại: {role_data['role_name']}")
    
    if created_count > 0:
        db.commit()
        logger.info(f"🎉 Đã tạo {created_count} role mới")
    
    return created_count


def init_admin_user(db: Session):
    """Khởi tạo tài khoản admin mặc định"""
    admin_email = "admin@cinema.com"
    admin_password = "Admin@123456"  # Mật khẩu mặc định, nên đổi sau khi đăng nhập
    
    # Kiểm tra admin đã tồn tại chưa
    existing_admin = db.query(Users).filter(Users.email == admin_email).first()
    
    if existing_admin:
        logger.info(f"ℹ️  Tài khoản admin đã tồn tại: {admin_email}")
        return False
    
    # Tạo tài khoản admin mới
    hashed_password = pwd_context.hash(admin_password)
    
    new_admin = Users(
        full_name="Super Admin",
        email=admin_email,
        password_hash=hashed_password,
        phone="0123456789",
        status=UserStatusEnum.active,
        is_verified=True,
        loyalty_points=0,
        total_spent=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    # Gán role super_admin
    super_admin_role = db.query(Role).filter(Role.role_name == "super_admin").first()
    if super_admin_role:
        user_role = UserRole(
            user_id=new_admin.user_id,
            role_id=super_admin_role.role_id
        )
        db.add(user_role)
        db.commit()
        
        logger.info(f"✅ Đã tạo tài khoản admin: {admin_email}")
        logger.info(f"📧 Email: {admin_email}")
        logger.info(f"🔑 Password: {admin_password}")
        logger.info(f"⚠️  VUI LÒNG ĐỔI MẬT KHẨU SAU KHI ĐĂNG NHẬP LẦN ĐẦU!")
        return True
    else:
        logger.error("❌ Không tìm thấy role super_admin")
        db.rollback()
        return False


def initialize_default_data(db: Session):
    """Khởi tạo tất cả dữ liệu mặc định"""
    logger.info("🚀 Bắt đầu khởi tạo dữ liệu mặc định...")
    
    try:
        # Tạo roles trước
        init_roles(db)
        
        # Tạo admin user
        init_admin_user(db)
        
        logger.info("✅ Hoàn thành khởi tạo dữ liệu mặc định!")
        
    except Exception as e:
        logger.error(f"❌ Lỗi khởi tạo dữ liệu: {str(e)}")
        db.rollback()
        raise
