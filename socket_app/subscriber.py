import json
import asyncio
import signal
import sys

from core.redis_client import redis_manager
from core.logger import get_logger
from socket_app.socket_manager import sio

logger = get_logger(__name__)

async def start_redis_subscriber():
    """Start the Redis subscriber as an asyncio background task"""
    pubsub = redis_manager.redis_client.pubsub()
    channels = ['market_data:exchange:1', 'market_data:exchange:2']
    await pubsub.subscribe(*channels)
    
    logger.info(f"Subscribed to channels: {channels}")

    try:
        async for message in pubsub.listen():
            await handle_market_data(message)
    except asyncio.CancelledError:
        logger.info("Redis subscriber cancelled")
    except Exception as e:
        logger.error(f"Subscriber error: {str(e)}")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()

async def handle_market_data(message):
    """Process and emit message via Socket.IO"""
    if message['type'] != 'message':
        return

    try:
        data = json.loads(message['data'])
        token = data.get('token')
        exchange_type = data.get('exchange_type')
        last_traded_price = data.get('last_traded_price')

        logger.info(f"Exchange: {exchange_type}, Token: {token}, LTP: {last_traded_price}")
        
        # Broadcast to all connected clients
        await sio.emit("market_data_update", data)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
