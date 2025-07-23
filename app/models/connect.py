from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ConnectRequest(Base):
    __tablename__ = "connect_request"
    id = Column(Integer, primary_key=True, index=True)
    # company_user_id를 nullable로 변경 (로그인하지 않은 사용자 지원)
    company_user_id = Column(Integer, nullable=True)  # 기업담당자 user_id (로그인 시에만)
    user_id = Column(Integer, nullable=False)  # 수료생 user_id
    # portfolio_id를 nullable로 변경 (자동으로 대표 포트폴리오 찾기)
    portfolio_id = Column(Integer, nullable=True)  # 포트폴리오 ID (자동 설정)
    
    # 기업담당자 기본 정보 (필수)
    company_representative_name = Column(String(100), nullable=False)  # 기업담당자 이름
    company_representative_email = Column(String(100), nullable=False)  # 기업담당자 이메일
    company_representative_phone = Column(String(20), nullable=False)  # 기업담당자 전화번호
    company_name = Column(String(100), nullable=True)  # 기업명
    
    # 채용 정보
    message = Column(Text, nullable=True)
    position = Column(String, nullable=True)  # 채용 포지션
    job_description = Column(String, nullable=True)  # 직무 설명
    required_stack = Column(String, nullable=True)  # 필수 기술 스택
    career_level = Column(String, nullable=True)  # 희망 경력 수준
    employment_type = Column(String, nullable=True)  # 고용 수준
    created_at = Column(DateTime, default=datetime.utcnow) 