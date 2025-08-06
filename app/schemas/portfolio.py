from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PortfolioBase(BaseModel):
    title: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    is_representative: bool = False

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioListResponse(BaseModel):
    portfolios: List[PortfolioResponse]
    total: int

    class Config:
        from_attributes = True 