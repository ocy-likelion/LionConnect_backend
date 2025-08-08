from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PortfolioBase(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    is_representative: bool = Field(False, description="대표 포트폴리오 여부")
    image: Optional[str] = Field(None, description="포트폴리오 이미지")
    project_url: Optional[str] = Field(None, description="프로젝트 URL")
    project_name: str = Field(..., description="프로젝트명", min_length=1, max_length=200)
    project_intro: str = Field(..., description="프로젝트 소개", min_length=1, max_length=500)
    project_period: str = Field(..., description="프로젝트 기간", min_length=1, max_length=100)
    role: str = Field(..., description="담당 역할", min_length=1, max_length=100)

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    is_representative: Optional[bool] = Field(None, description="대표 포트폴리오 여부")
    image: Optional[str] = Field(None, description="포트폴리오 이미지")
    project_url: Optional[str] = Field(None, description="프로젝트 URL")
    project_name: Optional[str] = Field(None, description="프로젝트명", min_length=1, max_length=200)
    project_intro: Optional[str] = Field(None, description="프로젝트 소개", min_length=1, max_length=500)
    project_period: Optional[str] = Field(None, description="프로젝트 기간", min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="담당 역할", min_length=1, max_length=100)

class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioListResponse(BaseModel):
    portfolios: List[PortfolioResponse]
    total: int

    class Config:
        from_attributes = True 