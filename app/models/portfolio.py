from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, nullable=False)  # 이력서(수료생) 참조
    is_representative = Column(Boolean, default=False)
    image = Column(String, nullable=True)
    project_url = Column(String, nullable=True)
    project_name = Column(String, nullable=False)
    project_intro = Column(String, nullable=False)
    project_period = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 