from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ResumeBasicInfo(Base):
    __tablename__ = "resume_basic_info"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    profile_image = Column(String, nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    job_type = Column(String, nullable=False)
    school = Column(String, nullable=False)
    major = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    period = Column(String, nullable=False)
    short_intro = Column(String, nullable=False)
    intro = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 