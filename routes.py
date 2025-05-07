from fastapi import APIRouter, Header, HTTPException, Depends
from models import RegisterUser, LoginUser
from auth import get_current_user, hash_password, register_user, login_user
from session import validate_session
from db import users_collection
from bson import ObjectId
from models import UpdateUserData
from db import users_collection
from bson import ObjectId



router = APIRouter()

@router.post("/register")
async def register(data: RegisterUser):
    return await register_user(data)

@router.post("/login")
async def login(data: LoginUser):
    return await login_user(data)



@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user["username"],
        "email": user["email"],
        "watchlist": user["watchlist"],
        "permissions": user["permissions"]
    }



@router.patch("/me/update")
async def update_user_data(
    payload: UpdateUserData,
    user_id: str = Depends(get_current_user)
):
    update_fields = {}

    if payload.watchlist is not None:
        update_fields["watchlist"] = [entry.model_dump() for entry in payload.watchlist]

    if payload.permissions is not None:
        update_fields["permissions"] = [entry.model_dump() for entry in payload.permissions]

    if payload.new_password is not None:
        update_fields["password_hash"] = await hash_password(payload.new_password)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No updates made")

    return {"message": "User data updated successfully"}
