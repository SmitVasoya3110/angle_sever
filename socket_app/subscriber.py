import json
import asyncio
import signal
import sys
from redis.asyncio import Redis
from core.redis_client import redis_manager
from core.logger import get_logger
from socket_app.socket_manager import sio

logger = get_logger(__name__)

# async def start_redis_subscriber():
#     """Start the Redis subscriber as an asyncio background task"""
#     pubsub = redis_manager.redis_client.pubsub()
#     channels = ['market_data:exchange:1', 'market_data:exchange:2']
#     await pubsub.subscribe(*channels)
    
#     logger.info(f"Subscribed to channels: {channels}")

#     try:
#         async for message in pubsub.listen():
#             await handle_market_data(message)
#     except asyncio.CancelledError:
#         logger.info("Redis subscriber cancelled")
#     except Exception as e:
#         logger.error(f"Subscriber error: {str(e)}")
#     finally:
#         await pubsub.unsubscribe()
#         await pubsub.close()

# async def handle_market_data(message):
#     """Process and emit message via Socket.IO"""
#     if message['type'] != 'message':
#         return

#     try:
#         data = json.loads(message['data'])
#         token = data.get('token')
#         exchange_type = data.get('exchange_type')
#         last_traded_price = data.get('last_traded_price')

#         logger.info(f"Exchange: {exchange_type}, Token: {token}, LTP: {last_traded_price}")
        
#         # Broadcast to all connected clients
#         await sio.emit("market_data_update", data)

#     except Exception as e:
#         logger.error(f"Error processing message: {str(e)}")

async def handle_market_data(message, sio=None):
    """Process market data messages, store in Redis and emit via Socket.IO"""
    try:
        if message['type'] != 'message':
            return

        data = json.loads(message['data'])

        base_key = f"market:{data['exchange_type']}:{data['token']}:{data['subscription_mode']}"

        latest_data = {
            'last_traded_price': data['last_traded_price'],
            'last_traded_quantity': data['last_traded_quantity'],
            'total_buy_quantity': data['total_buy_quantity'],
            'total_sell_quantity': data['total_sell_quantity'],
            'open_price': data['open_price_of_the_day'],
            'high_price': data['high_price_of_the_day'],
            'low_price': data['low_price_of_the_day'],
            'closed_price': data['closed_price'],
            'open_interest': data['open_interest'],
            'timestamp': data['exchange_timestamp']
        }

        best_buy = json.dumps(data['best_5_buy_data'])
        best_sell = json.dumps(data['best_5_sell_data'])
        latest_data['best_5_buy'] = best_buy
        latest_data['best_5_sell'] = best_sell
        print(latest_data)
        pipe = redis_manager.redis_client.pipeline()

        pipe.hset(f"{base_key}:latest", mapping=latest_data)
        price_ts_key = f"{base_key}:price_history"
        pipe.zadd(price_ts_key, {str(data['last_traded_price']): data['exchange_timestamp']})
        pipe.zremrangebyrank(price_ts_key, 0, -101)
        pipe.expire(f"{base_key}:latest", 86400)
        pipe.expire(price_ts_key, 86400)

        pipe.execute()

        # asyncio.create_task(write_to_file(data))

        # 🔥 Emit to all connected clients
        if sio:
            await sio.emit("market_data_update", data)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")



class AsyncRedisSubscriber:
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self.running = True

    async def connect(self):
        """Create async Redis connection"""
        try:
            redis_config = redis_manager.redis_client.connection_pool.connection_kwargs
            self.redis_client = Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                username=redis_config.get('username'),
                password=redis_config.get('password'),
                decode_responses=True,
                ssl=redis_config.get('ssl', False),
                max_connections=2  # Limit connections for subscriber
            )
            self.pubsub = self.redis_client.pubsub()
            logger.info("Async Redis connection established")
        except Exception as e:
            logger.error(f"Failed to create async Redis connection: {str(e)}")
            raise

    async def close(self):
        """Close Redis connections"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("Async Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing async Redis connections: {str(e)}")

    async def subscribe_to_channels(self):
        """Subscribe to Redis channels and process messages"""
        try:
            await self.connect()
            
            # Subscribe to both exchange types
            channels = ['market_data:exchange:1', 'market_data:exchange:2']
            await self.pubsub.subscribe(*channels)
            
            logger.info(f"Subscribed to channels: {channels}")
            logger.info("Waiting for messages... Press Ctrl+C to exit")
            
            # Start listening for messages asynchronously
            while self.running:
                message = await self.pubsub.get_message(timeout=1)
                if message:
                    print(message)
                    await handle_market_data(message)
                await asyncio.sleep(0.01)  # Small delay to prevent CPU overload
                
        except Exception as e:
            logger.error(f"Subscriber error: {str(e)}")
            raise
        finally:
            await self.close()
