from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # 추가
    # resume_id = Column(Integer, nullable=False)  # 1인 1이력서 구조라면 불필요
    is_representative = Column(Boolean, default=False)
    image = Column(String, nullable=True)
    project_url = Column(String, nullable=True)
    project_name = Column(String, nullable=False)
    project_intro = Column(String, nullable=False)
    project_period = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 