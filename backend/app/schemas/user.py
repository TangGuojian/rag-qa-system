from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    role: str
    expires_in: int


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    api_key: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    status: str
    api_key: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}
