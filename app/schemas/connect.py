from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConnectRequestCreate(BaseModel):
    company_user_id: int
    student_user_id: int
    portfolio_id: int
    message: Optional[str] = None

class ConnectRequestResponse(BaseModel):
    id: int
    company_user_id: int
    student_user_id: int
    portfolio_id: int
    message: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True 