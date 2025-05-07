import bcrypt
from datetime import datetime
from db import users_collection
from jwt_handler import create_jwt_tokens
from models import RegisterUser, LoginUser
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
from jwt_handler import SECRET_KEY, ALGORITHM


async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def register_user(data: RegisterUser):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = await hash_password(data.password)

    user_doc = {
        "username": data.username,
        "email": data.email,
        "password_hash": hashed,
        "watchlist": [entry.model_dump() for entry in data.watchlist],
        "permissions": [],
        "created_at": datetime.now(),
        "is_active": True
    }

    await users_collection.insert_one(user_doc)
    return {"message": "User registered successfully"}

async def login_user(data: LoginUser):
    user = await users_collection.find_one({"email": data.email})
    if not user or not await verify_password(data.password, user["password_hash"]):
        return {"error": "Invalid credentials"}

    access_token, refresh_token = create_jwt_tokens(str(user["_id"]))

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }




async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
