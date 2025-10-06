import asyncio
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.reservations_service import delete_expired_reservations

logger = logging.getLogger(__name__)

class BackgroundTasks:
    def __init__(self):
        self.running = False
        self.task = None

    async def cleanup_expired_reservations(self):
        """Background task to clean up expired seat reservations"""
        while self.running:
            try:
                db: Session = SessionLocal()
                try:
                    deleted_count = await delete_expired_reservations(db)
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} expired reservations")
                except Exception as e:
                    logger.error(f"Error cleaning up expired reservations: {e}")
                finally:
                    db.close()
                
                # Wait 30 seconds before next cleanup
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Unexpected error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def start(self):
        """Start the background cleanup task"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self.cleanup_expired_reservations())
            logger.info("Background cleanup task started")

    async def stop(self):
        """Stop the background cleanup task"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("Background cleanup task stopped")

# Global instance
background_tasks = BackgroundTasks()