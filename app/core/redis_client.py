import redis
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)

redis_client = None
if getattr(settings, 'REDIS_ENABLED', False):
    try:
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            password=getattr(settings, 'REDIS_PASSWORD', None),
            decode_responses=True
        )
        # Test kết nối
        if redis_client.ping():
            logger.info("Đã kết nối Redis thành công")
        else:
            logger.warning("Kết nối Redis thất bại (ping không trả về true)")
    except Exception as e:
        redis_client = None
        logger.warning(f"Không thể kết nối Redis: {e}")

def delete_pattern(pattern: str):
    if redis_client:
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)

if redis_client:
    redis_client.delete_pattern = delete_pattern
