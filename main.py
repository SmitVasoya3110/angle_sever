import asyncio
from fastapi import FastAPI
from routes import router
from socket_app.socket_manager import sio
from socketio import ASGIApp
# from socket_app.subscriber import start_redis_subscriber
from socket_app.subscriber import AsyncRedisSubscriber





fastapi_app = FastAPI()
fastapi_app.include_router(router)

app = ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)

# @fastapi_app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(start_redis_subscriber())

subscriber = AsyncRedisSubscriber()

@fastapi_app.on_event("startup")
async def startup_event():
    asyncio.create_task(subscriber.subscribe_to_channels())

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    subscriber.running = False