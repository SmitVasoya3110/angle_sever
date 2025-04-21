import redis.asyncio as redis

class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

# Create a singleton instance
redis_manager = RedisManager()