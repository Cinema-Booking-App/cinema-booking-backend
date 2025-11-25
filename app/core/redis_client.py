import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=getattr(settings, 'REDIS_DB', 0),
    password=getattr(settings, 'REDIS_PASSWORD', None),
    decode_responses=True
)

def delete_pattern(pattern: str):
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

redis_client.delete_pattern = delete_pattern
