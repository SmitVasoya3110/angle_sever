import uuid
import redis.asyncio as redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def create_session(user_id: str) -> str:
    session_key = str(uuid.uuid4())
    await redis_client.setex(f"session:{session_key}", 604800, user_id)  # 7 days
    return session_key

async def validate_session(session_key: str) -> str | None:
    return await redis_client.get(f"session:{session_key}")
