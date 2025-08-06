from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AwardBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None

class AwardCreate(AwardBase):
    pass

class AwardResponse(AwardBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 