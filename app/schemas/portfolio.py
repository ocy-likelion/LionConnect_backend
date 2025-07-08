from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class PortfolioBase(BaseModel):
    resume_id: int
    is_representative: Optional[bool] = False
    project_url: Optional[str] = None
    project_name: str
    project_intro: str
    project_period: str
    role: str

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    is_representative: Optional[bool] = None
    project_url: Optional[str] = None
    project_name: Optional[str] = None
    project_intro: Optional[str] = None
    project_period: Optional[str] = None
    role: Optional[str] = None
    # 이미지 교체는 별도 처리

class PortfolioResponse(PortfolioBase):
    id: int
    image: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 