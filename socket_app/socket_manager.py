import asyncio
import socketio
from motor.motor_asyncio import AsyncIOMotorClient
import os, json
import redis.asyncio as aioredis
from core.redis_client import redis_manager
from db import client,db

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

collection = db['temp']

# redis_client = aioredis.Redis(host='localhost', port=6379, db=0,decode_responses=True)
redis_client = redis_manager.redis_client



@sio.event
async def connect(sid, environ):
    print(f"Socket Connected: {sid}")



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



# Dictionary to store background tasks per client sid
client_tasks = {}

async def get_data_from_redis(tokens: list[str]) -> dict:
    data = {}
    for token in tokens:
        print(token)
        result = redis_client.hgetall(f"exchange:{token}")
        if result:
            data[token] = result
            print(f"{token}=======================",result)
    return data


# Background task to emit data repeatedly
async def emit_token_data(sid, tokens):
    try:
        while True:
            response = await get_data_from_redis(tokens)
            await sio.emit("tokens_data", response, to=sid)
            await asyncio.sleep(2)  # Send updates every 2 seconds
    except asyncio.CancelledError:
        print(f"[{sid}] Background task cancelled.")
        raise


@sio.on("subscribe_exchange_tokens")
async def subscribe_exchange_tokens(sid, data):
    tokens = data.get("tokens", [])
    print(f"[{sid}] Subscribed to tokens: {tokens}")

    # Cancel any existing task for this sid
    if sid in client_tasks:
        client_tasks[sid].cancel()
        await asyncio.sleep(0)  # Let the event loop process cancellation

    # Start a new background task
    task = asyncio.create_task(emit_token_data(sid, tokens))
    client_tasks[sid] = task


@sio.on("disconnect")
async def disconnect(sid):
    print(f"[{sid}] Disconnected.")
    # Cancel background task when client disconnects
    if sid in client_tasks:
        client_tasks[sid].cancel()
        del client_tasks[sid]
