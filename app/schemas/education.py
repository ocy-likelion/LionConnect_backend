from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EducationResponse(BaseModel):
    id: int
    resume_id: int
    institution: str
    period: str
    name: str
    created_at: datetime
    class Config:
        orm_mode = True 