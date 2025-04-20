from fastapi import APIRouter, Header, HTTPException, Depends
from models import UserRegister, UserLogin
from auth import register_user, login_user
from session import validate_session
from db import users_collection
from bson import ObjectId

router = APIRouter()

@router.post("/register")
async def register(data: UserRegister):
    return await register_user(data)

@router.post("/login")
async def login(data: UserLogin):
    return await login_user(data)

async def get_current_user(session_key: str = Header(...)):
    user_id = await validate_session(session_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_id

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return {"email": user["email"]}
