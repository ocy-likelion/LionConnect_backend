from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AwardBase(BaseModel):
    resume_id: int = Field(..., description="이력서 ID")
    name: str = Field(..., description="수상/자격증명", min_length=1, max_length=200)
    date: str = Field(..., description="취득일", min_length=1, max_length=100)
    organization: str = Field(..., description="기관명", min_length=1, max_length=200)

class AwardCreate(AwardBase):
    pass

class AwardUpdate(BaseModel):
    name: Optional[str] = Field(None, description="수상/자격증명", min_length=1, max_length=200)
    date: Optional[str] = Field(None, description="취득일", min_length=1, max_length=100)
    organization: Optional[str] = Field(None, description="기관명", min_length=1, max_length=200)

class AwardResponse(AwardBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 