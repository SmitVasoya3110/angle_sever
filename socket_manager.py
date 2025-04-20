# socket_manager.py
import asyncio
import socketio
from motor.motor_asyncio import AsyncIOMotorClient
import os, json
import redis.asyncio as aioredis

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["android_app"]
collection = db["temp"]

redis_client = aioredis.Redis(host='localhost', port=6379, db=0,decode_responses=True)

@sio.event
async def connect(sid, environ):
    print(f"Socket Connected: {sid}")

# @sio.event
# async def disconnect(sid):
#     print(f"Socket Disconnected: {sid}")

@sio.event
async def search_query(sid, data):

    query = data.get("query", "")
    if not query:
        await sio.emit("search_results", {"results": []}, to=sid)
        return

    cursor = collection.find({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"symbol": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # convert ObjectId
        results.append(doc)

    await sio.emit("search_results", {"results": results}, to=sid)


# Store connected background tasks to cancel on disconnect
active_tasks = {}

@sio.on("subscribe_tokens")
async def subscribe_tokens(sid, data):
    tokens = data.get("tokens", [])
    if not tokens:
        await sio.emit("token_stream", {"error": "No tokens provided"}, to=sid)
        return

    print(f"🔗 Client {sid} subscribed to tokens: {tokens}")

    async def send_filtered_data():
        while True:
            try:
                # Get and decode stocks from Redis
                stocks_raw = await redis_client.get("Stocks")
                if stocks_raw:
                    all_stocks = json.loads(stocks_raw)
                    # Filter by tokens
                    filtered = [stock for stock in all_stocks if stock["token"] in tokens]
                    await sio.emit("token_stream", {"data": filtered}, to=sid)
            except Exception as e:
                print(f"Error in token stream: {e}")
                await sio.emit("token_stream", {"error": str(e)}, to=sid)

            await asyncio.sleep(3)

    # Start background task
    task = asyncio.create_task(send_filtered_data())
    active_tasks[sid] = task



# @sio.event
# async def subscribe_exchange_tokens(sid, data):

#     tokens = data.get("tokens", [])
#     print(f"Received subscription for tokens: {tokens}")

#     try:
#         while True:
#             response = {}
#             for token in tokens:
#                 key = f"exchange:{token}"
#                 if redis_client.exists(key):
#                     response[token] = redis_client.hgetall(key)
#             await sio.emit("tokens_data", response, to=sid)
#             await asyncio.sleep(3) 
#     except asyncio.CancelledError:
#         print(f"Stopped streaming for: {sid}")



@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    task = active_tasks.pop(sid, None)
    if task:
        task.cancel()


async def get_data_from_redis(tokens: list[str]) -> dict:
    data = {}
    for token in tokens:
        result = await redis_client.hgetall(f"exchange:{token}")
        if result:
            data[token] = result
    return data

# Socket.IO event handler
@sio.on("subscribe_exchange_tokens")
async def subscribe_exchange_tokens(sid, data):
    tokens = data.get("tokens", [])
    print(f"[{sid}] Subscribed to tokens: {tokens}")

    response = await get_data_from_redis(tokens)
    print("response: ", response)
    await sio.emit("tokens_data", response, to=sid)