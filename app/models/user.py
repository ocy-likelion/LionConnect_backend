from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserTypeEnum(str, enum.Enum):
    student = "student"
    company = "company"

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    user_type = Column(Enum(UserTypeEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student_profile = relationship("StudentProfile", uselist=False, back_populates="user")
    company_profile = relationship("CompanyProfile", uselist=False, back_populates="user")

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