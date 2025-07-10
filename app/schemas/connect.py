from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConnectRequestCreate(BaseModel):
    company_user_id: int
    student_user_id: int
    portfolio_id: int
    message: Optional[str] = None
    position: Optional[str] = None
    job_description: Optional[str] = None
    required_stack: Optional[str] = None
    career_level: Optional[str] = None
    employment_type: Optional[str] = None

class ConnectRequestResponse(BaseModel):
    id: int
    company_user_id: int
    student_user_id: int
    portfolio_id: int
    message: Optional[str]
    position: Optional[str]
    job_description: Optional[str]
    required_stack: Optional[str]
    career_level: Optional[str]
    employment_type: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True 