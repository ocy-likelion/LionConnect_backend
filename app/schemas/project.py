from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    portfolio_id: int = Field(..., description="포트폴리오 ID")
    project_name: str = Field(..., description="프로젝트명")
    project_period: str = Field(..., description="프로젝트 기간")
    project_intro: str = Field(..., description="프로젝트 소개")
    description: str = Field(..., description="프로젝트 설명")
    role: str = Field(..., description="담당 역할")
    tech_stack: str = Field(..., description="기술 스택")
    user_id: int = Field(..., description="사용자 ID")
    github_url: Optional[str] = Field(None, description="GitHub URL")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    portfolio_id: Optional[int] = Field(None, description="포트폴리오 ID")
    project_name: Optional[str] = Field(None, description="프로젝트명")
    project_period: Optional[str] = Field(None, description="프로젝트 기간")
    project_intro: Optional[str] = Field(None, description="프로젝트 소개")
    description: Optional[str] = Field(None, description="프로젝트 설명")
    role: Optional[str] = Field(None, description="담당 역할")
    tech_stack: Optional[str] = Field(None, description="기술 스택")
    github_url: Optional[str] = Field(None, description="GitHub URL")

class ProjectResponse(BaseModel):
    id: int
    portfolio_id: int
    project_name: str
    project_period: str
    project_intro: str
    description: str
    role: str
    tech_stack: str
    user_id: int
    github_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int

    class Config:
        from_attributes = True 