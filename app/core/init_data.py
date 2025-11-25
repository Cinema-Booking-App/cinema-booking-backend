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
from app.models.permissions import Permission

def init_roles(db: Session):
    """Khởi tạo các role mặc định (idempotent & chống race condition)"""
    default_roles = [
        {"role_name": "super_admin", "description": "Quản trị viên cấp cao - toàn quyền quản lý hệ thống"},
        {"role_name": "theater_admin", "description": "Quản trị viên rạp - quản lý rạp chiếu phim"},
        {"role_name": "theater_manager", "description": "Quản lý rạp - quản lý suất chiếu và vận hành"},
        {"role_name": "user", "description": "Người dùng thông thường"},
        {"role_name": "booking_staff", "description": "Nhân viên bán vé / quản lý quầy - xử lý bán vé tại quầy"},
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

    # Lấy rank Bronze mặc định
    from app.models.ranks import Ranks
    bronze_rank = db.query(Ranks).filter(Ranks.rank_name == "Bronze").first()
    new_admin = Users(
        full_name="Super Admin",
        email=admin_email,
        password_hash=hashed_password,
        phone=admin_phone,
        status=UserStatusEnum.active,
        is_verified=True,
        loyalty_points=0,
        total_spent=0,
        rank_id=bronze_rank.rank_id if bronze_rank else None,
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

        # Tạo các rank mặc định
        try:
            init_ranks(db)
        except Exception as e:
            logger.warning(f"⚠️ Không thể khởi tạo các rank mặc định: {e}")

        # Tạo admin user
        init_admin_user(db)

        # Tạo nhân viên quản lý quầy (booking staff)
        try:
            init_counter_user(db)
        except Exception as e:
            logger.warning(f"⚠️ Không thể khởi tạo counter staff mặc định: {e}")

        # Tạo permission 'counter' và gán cho role booking_staff
        try:
            init_counter_permission(db)
        except Exception as e:
            logger.warning(f"⚠️ Không thể khởi tạo permission counter: {e}")

        logger.info("✅ Hoàn thành khởi tạo dữ liệu mặc định!")

    except Exception as e:
        logger.error(f"❌ Lỗi khởi tạo dữ liệu: {str(e)}")
        db.rollback()
        raise
def init_ranks(db: Session):
    """Khởi tạo các rank mặc định cho hệ thống"""
    from app.models.ranks import Ranks
    default_ranks = [
        {
            "rank_name": "Bronze",
            "spending_target": 0,
            "ticket_percent": 1,
            "combo_percent": 1,
            "is_default": True
        },
        {
            "rank_name": "Silver",
            "spending_target": 2000000,
            "ticket_percent": 2,
            "combo_percent": 2,
            "is_default": False
        },
        {
            "rank_name": "Gold",
            "spending_target": 5000000,
            "ticket_percent": 3,
            "combo_percent": 3,
            "is_default": False
        },
        {
            "rank_name": "Platinum",
            "spending_target": 10000000,
            "ticket_percent": 4,
            "combo_percent": 4,
            "is_default": False
        },
        {
            "rank_name": "Diamond",
            "spending_target": 20000000,
            "ticket_percent": 5,
            "combo_percent": 5,
            "is_default": False
        },
    ]
    created_count = 0
    for rank_data in default_ranks:
        existing_rank = db.query(Ranks).filter(Ranks.rank_name == rank_data["rank_name"]).first()
        if existing_rank:
            logger.info(f"ℹ️ Rank đã tồn tại: {rank_data['rank_name']}")
            continue
        try:
            new_rank = Ranks(**rank_data)
            db.add(new_rank)
            db.flush()
            created_count += 1
            logger.info(f"✅ Tạo rank: {rank_data['rank_name']}")
        except IntegrityError:
            db.rollback()
            logger.info(f"⚠️ Race condition – rank đã được tạo bởi worker khác: {rank_data['rank_name']}")
    if created_count > 0:
        try:
            db.commit()
            logger.info(f"🎉 Đã tạo {created_count} rank mới")
        except IntegrityError:
            db.rollback()
            logger.warning("⚠️ Commit ranks gặp lỗi, có thể do worker khác commit trước. Bỏ qua.")
    return created_count


def init_counter_user(db: Session):
    """Khởi tạo tài khoản nhân viên quầy mặc định (idempotent & chống race condition)"""
    counter_email = "counter@cinema.com"
    counter_phone = "0123456799"
    counter_password = "Counter@123"  # Khuyến nghị đổi sau khi nhận

    existing = db.query(Users).filter(Users.email == counter_email).first()
    if existing:
        logger.info(f"ℹ️ Counter staff đã tồn tại theo email: {counter_email}")
        # đảm bảo có role booking_staff
        booking_role = db.query(Role).filter(Role.role_name == "booking_staff").first()
        if booking_role and not any(r.role_name == "booking_staff" for r in existing.roles):
            try:
                db.add(UserRole(user_id=existing.user_id, role_id=booking_role.role_id))
                db.commit()
                logger.info("✅ Đã gán role booking_staff cho user hiện có")
            except IntegrityError:
                db.rollback()
                logger.warning("⚠️ Race condition khi gán role booking_staff, bỏ qua")
        return False

    # Hash mật khẩu
    hashed_password = pwd_context.hash(counter_password)

    # Lấy rank Bronze mặc định
    from app.models.ranks import Ranks
    bronze_rank = db.query(Ranks).filter(Ranks.rank_name == "Bronze").first()
    new_user = Users(
        full_name="Counter Staff",
        email=counter_email,
        password_hash=hashed_password,
        phone=counter_phone,
        status=UserStatusEnum.active,
        is_verified=True,
        loyalty_points=0,
        total_spent=0,
        rank_id=bronze_rank.rank_id if bronze_rank else None,
    )

    try:
        db.add(new_user)
        db.flush()
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"⚠️ Race condition tạo counter staff hoặc trùng dữ liệu: {e}. Thử lấy lại user hiện có.")
        existing_user = db.query(Users).filter(Users.email == counter_email).first() or \
                        db.query(Users).filter(Users.phone == counter_phone).first()
        if existing_user:
            logger.info("ℹ️ Counter staff đã được worker khác tạo, bỏ qua.")
            return False
        else:
            raise

    # Gán role booking_staff
    booking_role = db.query(Role).filter(Role.role_name == "booking_staff").first()
    if not booking_role:
        logger.error("❌ Không tìm thấy role booking_staff, hủy tạo counter staff.")
        db.rollback()
        return False

    try:
        db.add(UserRole(user_id=new_user.user_id, role_id=booking_role.role_id))
        db.commit()
        logger.info(f"✅ Đã tạo tài khoản counter staff: {counter_email}")
        logger.info(f"🔑 Password: {counter_password}")
        return True
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"⚠️ Race condition khi gán role booking_staff cho user mới: {e}")
        return False


def init_counter_permission(db: Session):
    """Ensure the 'counter' permission exists and is assigned to 'booking_staff' role."""
    perm_name = 'counter'
    # Create permission if not exists
    permission = db.query(Permission).filter(Permission.permission_name == perm_name).first()
    if not permission:
        try:
            permission = Permission(
                permission_name=perm_name,
                description='Quản lý chức năng quầy (tra cứu, in vé, xác nhận)',
                module='counter',
                actions=['view', 'operate']
            )
            db.add(permission)
            db.flush()
            db.commit()
            logger.info(f"✅ Tạo permission: {perm_name}")
        except IntegrityError:
            db.rollback()
            permission = db.query(Permission).filter(Permission.permission_name == perm_name).first()

    # Assign permission to booking_staff role
    booking_role = db.query(Role).filter(Role.role_name == 'booking_staff').first()
    if not booking_role:
        logger.warning("⚠️ Không tìm thấy role booking_staff để gán permission counter")
        return False

    # Check if already assigned
    try:
        assigned_names = [p.permission_name for p in getattr(booking_role, 'permissions', [])]
        if perm_name in assigned_names:
            logger.info("ℹ️ Permission 'counter' đã được gán cho role booking_staff")
            return True
    except Exception:
        pass

    try:
        booking_role.permissions.append(permission)
        db.add(booking_role)
        db.commit()
        logger.info("✅ Đã gán permission 'counter' cho role booking_staff")
        return True
    except IntegrityError:
        db.rollback()
        logger.warning("⚠️ Race condition khi gán permission 'counter' cho role booking_staff, bỏ qua")
        return False
