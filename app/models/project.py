from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, nullable=False)  # 포트폴리오 참조
    project_name = Column(String, nullable=False)
    project_period = Column(String, nullable=False)
    project_intro = Column(String, nullable=False)
    description = Column(String, nullable=False)
    role = Column(String, nullable=False)
    tech_stack = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    github_url = Column(String, nullable=True)  # github url 