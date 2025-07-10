from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ConnectRequest(Base):
    __tablename__ = "connect_request"
    id = Column(Integer, primary_key=True, index=True)
    company_user_id = Column(Integer, nullable=False)  # 기업담당자 user_id
    student_user_id = Column(Integer, nullable=False)  # 수료생 user_id
    portfolio_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    position = Column(String, nullable=True)  # 채용 포지션
    job_description = Column(String, nullable=True)  # 직무 설명
    required_stack = Column(String, nullable=True)  # 필수 기술 스택
    career_level = Column(String, nullable=True)  # 희망 경력 수준
    employment_type = Column(String, nullable=True)  # 고용 수준
    created_at = Column(DateTime, default=datetime.utcnow) 