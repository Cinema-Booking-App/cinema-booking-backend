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

from sqlalchemy.exc import IntegrityError

def init_roles(db: Session):
    """Khởi tạo các role mặc định (idempotent & chống race condition)"""
    default_roles = [
        {"role_name": "super_admin", "description": "Quản trị viên cấp cao - toàn quyền quản lý hệ thống"},
        {"role_name": "theater_admin", "description": "Quản trị viên rạp - quản lý rạp chiếu phim"},
        {"role_name": "theater_manager", "description": "Quản lý rạp - quản lý suất chiếu và vận hành"},
        {"role_name": "user", "description": "Người dùng thông thường"},
    ]

    created_count = 0
    for role_data in default_roles:
        existing_role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()
        if existing_role:
            logger.info(f"ℹ️ Role đã tồn tại: {role_data['role_name']}")
            continue
        # Thử tạo, nếu race condition xảy ra thì bỏ qua
        try:
            new_role = Role(**role_data)
            db.add(new_role)
            db.flush()  # lấy id mà chưa commit toàn bộ
            created_count += 1
            logger.info(f"✅ Tạo role: {role_data['role_name']}")
        except IntegrityError:
            db.rollback()
            logger.info(f"⚠️ Race condition – role đã được tạo bởi worker khác: {role_data['role_name']}")

    if created_count > 0:
        try:
            db.commit()
            logger.info(f"🎉 Đã tạo {created_count} role mới")
        except IntegrityError:
            db.rollback()
            logger.warning("⚠️ Commit roles gặp lỗi, có thể do worker khác commit trước. Bỏ qua.")

    return created_count


def init_admin_user(db: Session):
    """Khởi tạo tài khoản admin mặc định (idempotent & chống race condition)"""
    admin_email = "admin@cinema.com"
    admin_phone = "0123456788"
    admin_password = "Admin@123456"  # Mật khẩu mặc định, nên đổi sau khi đăng nhập

    # Kiểm tra tồn tại theo email trước
    existing_admin = db.query(Users).filter(Users.email == admin_email).first()
    if existing_admin:
        logger.info(f"ℹ️ Admin đã tồn tại theo email: {admin_email}")
        # Đảm bảo có role super_admin
        super_admin_role = db.query(Role).filter(Role.role_name == "super_admin").first()
        if super_admin_role and not any(r.role_name == "super_admin" for r in existing_admin.roles):
            try:
                db.add(UserRole(user_id=existing_admin.user_id, role_id=super_admin_role.role_id))
                db.commit()
                logger.info("✅ Đã gán thêm role super_admin cho admin hiện có")
            except IntegrityError:
                db.rollback()
                logger.warning("⚠️ Race condition khi gán role super_admin, bỏ qua")
        return False

    # Hash mật khẩu
    hashed_password = pwd_context.hash(admin_password)

    new_admin = Users(
        full_name="Super Admin",
        email=admin_email,
        password_hash=hashed_password,
        phone=admin_phone,
        status=UserStatusEnum.active,
        is_verified=True,
        loyalty_points=0,
        total_spent=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    try:
        db.add(new_admin)
        db.flush()  # Lấy user_id mà chưa commit toàn bộ để có thể rollback nếu lỗi
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"⚠️ Race condition tạo admin hoặc trùng dữ liệu: {e}. Thử lấy lại user hiện có.")
        existing_admin = db.query(Users).filter(Users.email == admin_email).first() or \
                        db.query(Users).filter(Users.phone == admin_phone).first()
        if existing_admin:
            logger.info("ℹ️ Admin đã được worker khác tạo, bỏ qua.")
            return False
        else:
            raise

    # Gán role super_admin
    super_admin_role = db.query(Role).filter(Role.role_name == "super_admin").first()
    if not super_admin_role:
        logger.error("❌ Không tìm thấy role super_admin, hủy tạo admin.")
        db.rollback()
        return False

    try:
        db.add(UserRole(user_id=new_admin.user_id, role_id=super_admin_role.role_id))
        db.commit()
        logger.info(f"✅ Đã tạo tài khoản admin: {admin_email}")
        logger.info(f"📧 Email: {admin_email}")
        logger.info(f"🔑 Password: {admin_password}")
        logger.info("⚠️ Vui lòng đổi mật khẩu sau khi đăng nhập lần đầu!")
        return True
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"⚠️ Race condition khi gán role super_admin cho admin mới: {e}")
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
