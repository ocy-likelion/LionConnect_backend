from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserTypeEnum

class UserBase(BaseModel):
    email: EmailStr

class UserCreateStudent(UserBase):
    password: str
    name: str

class UserCreateCompany(UserBase):
    password: str
    name: str
    company_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    user_type: UserTypeEnum
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse