"""
Background Tasks - Các tác vụ chạy nền cho hệ thống realtime
File này quản lý các tác vụ chạy nền, chủ yếu để dọn dẹp ghế hết hạn và gửi thông báo WebSocket
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.reservations_service import delete_expired_reservations

logger = logging.getLogger(__name__)


class BackgroundTasks:
    """Lớp quản lý các tác vụ chạy nền cho hệ thống đặt vé realtime"""
    
    def __init__(self):
        self.running = False  # Trạng thái chạy của tác vụ nền
        self.task = None      # Task asyncio đang chạy

    async def cleanup_expired_reservations(self):
        """Tác vụ nền: Dọn dẹp các ghế đặt chỗ hết hạn và gửi thông báo WebSocket realtime"""
        while self.running:
            try:
                # Tạo session database mới cho mỗi lần dọn dẹp
                db: Session = SessionLocal()
                try:
                    # Gọi service để xóa ghế hết hạn (service sẽ tự động gửi WebSocket)
                    deleted_count = await delete_expired_reservations(db)
                    if deleted_count > 0:
                        logger.info(f"🧹 Đã dọn dẹp {deleted_count} ghế hết hạn (realtime notification sent)")
                except Exception as e:
                    logger.error(f"❌ Lỗi khi dọn dẹp ghế hết hạn: {e}")
                finally:
                    db.close()  # Đảm bảo đóng connection
                
                # Chờ 30 giây trước lần dọn dẹp tiếp theo
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Lỗi không mong muốn trong tác vụ dọn dẹp: {e}")
                await asyncio.sleep(60)  # Chờ lâu hơn khi có lỗi

    def start(self):
        """Khởi động tác vụ dọn dẹp nền"""
        if not self.running:
            self.running = True
            # Tạo task asyncio để chạy đồng thời với server chính
            self.task = asyncio.create_task(self.cleanup_expired_reservations())
            logger.info("🚀 Tác vụ dọn dẹp nền đã khởi động (30s interval)")

    async def stop(self):
        """Dừng tác vụ dọn dẹp nền"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()  # Hủy task
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass  # Task đã được hủy thành công
            logger.info("🛑 Tác vụ dọn dẹp nền đã dừng")


# Instance toàn cục để sử dụng trong toàn bộ ứng dụng
background_tasks = BackgroundTasks()