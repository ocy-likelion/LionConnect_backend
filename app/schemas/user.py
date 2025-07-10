from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserTypeEnum, OAuthProviderEnum

class UserBase(BaseModel):
    email: EmailStr

class UserCreateStudent(UserBase):
    password: str
    course_name: str
    course_generation: str
    tech_stack: str

class UserCreateCompany(UserBase):
    password: str
    company_name: str
    industry: str
    size: str
    intro: str

class UserResponse(BaseModel):
    id: int
    email: str
    user_type: UserTypeEnum
    oauth_provider: Optional[OAuthProviderEnum] = None
    name: Optional[str] = None
    profile_image: Optional[str] = None
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

class OAuthLoginRequest(BaseModel):
    user_type: UserTypeEnum = UserTypeEnum.student

class OAuthCallbackResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_new_user: bool = False 