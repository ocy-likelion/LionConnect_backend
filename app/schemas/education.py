from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EducationBase(BaseModel):
    resume_id: int = Field(..., description="이력서 ID")
    institution: str = Field(..., description="교육 기관", min_length=1, max_length=200)
    period: str = Field(..., description="교육 기간", min_length=1, max_length=100)
    name: str = Field(..., description="교육명", min_length=1, max_length=200)

class EducationCreate(EducationBase):
    pass

class EducationUpdate(BaseModel):
    institution: Optional[str] = Field(None, description="교육 기관", min_length=1, max_length=200)
    period: Optional[str] = Field(None, description="교육 기간", min_length=1, max_length=100)
    name: Optional[str] = Field(None, description="교육명", min_length=1, max_length=200)

class EducationResponse(EducationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 