# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True