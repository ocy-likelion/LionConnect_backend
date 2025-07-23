from pydantic import BaseModel, EmailStr, constr, ConfigDict
from typing import Optional
from datetime import datetime

class ResumeBasicInfoBase(BaseModel):
    name: str
    email: EmailStr
    phone: constr(min_length=10, max_length=15)
    job_type: str
    school: str
    major: str
    grade: str
    period: str
    short_intro: str
    intro: str
    age: Optional[int]

class ResumeBasicInfoCreate(ResumeBasicInfoBase):
    pass

class ResumeBasicInfoResponse(ResumeBasicInfoBase):
    id: int
    profile_image: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 