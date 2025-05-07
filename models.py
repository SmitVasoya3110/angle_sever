from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class RegisterUser(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginUser(BaseModel):
    email: EmailStr
    password: str


class WatchlistEntry(BaseModel):
    exchange: str
    tokens: List[int]


class PermissionEntry(BaseModel):
    exchange: str
    script_token: int
    max_margin: float
    max_quantity: int


class RegisterUser(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    watchlist: Optional[List[WatchlistEntry]] = []  # default to empty list if not provided


class UpdateUserData(BaseModel):
    watchlist: Optional[List[WatchlistEntry]] = None
    permissions: Optional[List[PermissionEntry]] = None
    new_password: Optional[str] = Field(None, min_length=6)