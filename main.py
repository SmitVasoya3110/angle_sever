from fastapi import FastAPI
from routes import router
from socket_manager import sio
from socketio import ASGIApp

fastapi_app = FastAPI()
fastapi_app.include_router(router)

app = ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
