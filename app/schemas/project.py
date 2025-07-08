from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    portfolio_id: int
    project_name: str
    project_period: str
    project_intro: str
    description: str
    role: str
    tech_stack: str
    github_url: Optional[str]

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_period: Optional[str] = None
    project_intro: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    tech_stack: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 