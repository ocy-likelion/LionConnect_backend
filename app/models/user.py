from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import bcrypt

Base = declarative_base()

class UserTypeEnum(str, enum.Enum):
    student = "student"
    company = "company"

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # 기본 로그인이므로 비밀번호 필수
    name = Column(String, nullable=False)  # 사용자 이름 필수
    user_type = Column(Enum(UserTypeEnum), nullable=False)
    
    # 기업 사용자 전용 필드
    company_name = Column(String, nullable=True)  # 기업 사용자만 사용
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student_profile = relationship("StudentProfile", uselist=False, back_populates="user")
    company_profile = relationship("CompanyProfile", uselist=False, back_populates="user")

    def set_password(self, password: str):
        """비밀번호를 해시화하여 저장"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """비밀번호 확인"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

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