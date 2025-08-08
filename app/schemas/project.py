from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    project_name: str = Field(..., description="프로젝트명", min_length=1, max_length=200)
    project_period: str = Field(..., description="프로젝트 기간", min_length=1, max_length=100)
    project_intro: str = Field(..., description="프로젝트 소개", min_length=1, max_length=500)
    description: str = Field(..., description="프로젝트 설명", min_length=1, max_length=1000)
    role: str = Field(..., description="담당 역할", min_length=1, max_length=100)
    tech_stack: str = Field(..., description="기술 스택", min_length=1, max_length=200)
    user_id: int = Field(..., description="사용자 ID", gt=0)
    github_url: Optional[str] = Field(None, description="GitHub URL", max_length=500)

    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('사용자 ID는 0보다 커야 합니다')
        return v

    @validator('github_url')
    def validate_github_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('GitHub URL은 http:// 또는 https://로 시작해야 합니다')
        return v

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, description="프로젝트명", min_length=1, max_length=200)
    project_period: Optional[str] = Field(None, description="프로젝트 기간", min_length=1, max_length=100)
    project_intro: Optional[str] = Field(None, description="프로젝트 소개", min_length=1, max_length=500)
    description: Optional[str] = Field(None, description="프로젝트 설명", min_length=1, max_length=1000)
    role: Optional[str] = Field(None, description="담당 역할", min_length=1, max_length=100)
    tech_stack: Optional[str] = Field(None, description="기술 스택", min_length=1, max_length=200)
    github_url: Optional[str] = Field(None, description="GitHub URL", max_length=500)

    @validator('github_url')
    def validate_github_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('GitHub URL은 http:// 또는 https://로 시작해야 합니다')
        return v

class ProjectResponse(BaseModel):
    id: int
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