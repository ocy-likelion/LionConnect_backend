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
    created_at = Column(DateTime, default=datetime.utcnow) 