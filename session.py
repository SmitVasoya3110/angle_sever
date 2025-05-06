import uuid
import redis.asyncio as redis
from core.redis_client import redis_manager

# redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
redis_client = redis_manager.redis_client


async def create_session(user_id: str) -> str:
    session_key = str(uuid.uuid4())
    redis_client.setex(f"session:{session_key}", 604800, user_id)  # 7 days
    return session_key

async def validate_session(session_key: str) -> str | None:
    return redis_client.get(f"session:{session_key}")
