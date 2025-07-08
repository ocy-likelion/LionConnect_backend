from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Award(Base):
    __tablename__ = "award"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, nullable=False)  # 이력서 참조
    name = Column(String, nullable=False)        # 수상/자격증 명
    date = Column(String, nullable=False)        # 취득일
    organization = Column(String, nullable=False) # 기관명
    created_at = Column(DateTime, default=datetime.utcnow) 