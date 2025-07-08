from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AwardResponse(BaseModel):
    id: int
    resume_id: int
    name: str
    date: str
    organization: str
    created_at: datetime
    class Config:
        orm_mode = True 