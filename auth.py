import bcrypt
from db import users_collection
from session import create_session

async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def register_user(data):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        return {"error": "User already exists"}

    hashed = await hash_password(data.password)
    await users_collection.insert_one({"email": data.email, "password": hashed})
    return {"message": "Registered"}

async def login_user(data):
    user = await users_collection.find_one({"email": data.email})
    if not user or not await verify_password(data.password, user["password"]):
        return {"error": "Invalid credentials"}

    session_key = await create_session(str(user["_id"]))
    return {"message": "Login successful", "session_key": session_key}
