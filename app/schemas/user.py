from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime

class UserTypeEnum(str, Enum):
    student = "student"
    company = "company"

class StudentProfileCreate(BaseModel):
    course_name: str
    course_generation: str
    tech_stack: str

class CompanyProfileCreate(BaseModel):
    company_name: str
    industry: str
    size: str
    intro: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    user_type: UserTypeEnum

class UserCreateStudent(UserBase, StudentProfileCreate):
    password: str

class UserCreateCompany(UserBase, CompanyProfileCreate):
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    user_type: UserTypeEnum
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" 