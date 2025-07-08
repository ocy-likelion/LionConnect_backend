from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, nullable=False)  # 이력서 참조
    institution = Column(String, nullable=False) # 교육 기관
    period = Column(String, nullable=False)      # 교육 기간
    name = Column(String, nullable=False)        # 교육 명
    created_at = Column(DateTime, default=datetime.utcnow) 