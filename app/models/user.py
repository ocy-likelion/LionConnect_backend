from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserTypeEnum(str, enum.Enum):
    student = "student"
    company = "company"

class OAuthProviderEnum(str, enum.Enum):
    google = "google"
    kakao = "kakao"

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # 소셜 로그인 사용자는 비밀번호가 없을 수 있음
    user_type = Column(Enum(UserTypeEnum), nullable=False)
    
    # OAuth 관련 필드
    oauth_provider = Column(Enum(OAuthProviderEnum), nullable=True)
    oauth_id = Column(String, nullable=True)  # OAuth 제공자의 사용자 ID
    name = Column(String, nullable=True)  # OAuth에서 가져온 이름
    profile_image = Column(String, nullable=True)  # OAuth에서 가져온 프로필 이미지
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student_profile = relationship("StudentProfile", uselist=False, back_populates="user")
    company_profile = relationship("CompanyProfile", uselist=False, back_populates="user")

    # OAuth ID와 제공자로 유니크 인덱스 생성
    __table_args__ = (
        # OAuth 사용자는 provider + oauth_id 조합이 유니크해야 함
        # 일반 사용자는 email이 유니크해야 함
    )

class StudentProfile(Base):
    __tablename__ = "student_profile"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    course_name = Column(String, nullable=False)
    course_generation = Column(String, nullable=False)
    tech_stack = Column(String, nullable=False)
    user = relationship("User", back_populates="student_profile")

class CompanyProfile(Base):
    __tablename__ = "company_profile"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    company_name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    size = Column(String, nullable=False)
    intro = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
    user = relationship("User", back_populates="company_profile") 