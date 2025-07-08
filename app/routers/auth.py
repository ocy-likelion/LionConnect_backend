from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreateStudent, UserCreateCompany, UserResponse, LoginRequest, TokenResponse, UserTypeEnum
from app.models.user import User, StudentProfile, CompanyProfile
from app.core.config import SessionLocal
from app.utils.auth import hash_password, verify_password, create_access_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup/student", response_model=UserResponse)
def signup_student(user: UserCreateStudent, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user_obj = User(
        email=user.email,
        password_hash=hash_password(user.password),
        user_type=UserTypeEnum.student,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    profile = StudentProfile(
        user_id=user_obj.id,
        course_name=user.course_name,
        course_generation=user.course_generation,
        tech_stack=user.tech_stack,
    )
    db.add(profile)
    db.commit()
    return user_obj

@router.post("/signup/company", response_model=UserResponse)
def signup_company(user: UserCreateCompany, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user_obj = User(
        email=user.email,
        password_hash=hash_password(user.password),
        user_type=UserTypeEnum.company,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    profile = CompanyProfile(
        user_id=user_obj.id,
        company_name=user.company_name,
        industry=user.industry,
        size=user.size,
        intro=user.intro,
        email_verified=False,
    )
    db.add(profile)
    db.commit()
    return user_obj

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    return TokenResponse(access_token=access_token) 