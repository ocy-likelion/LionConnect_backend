from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from sqlalchemy.orm import Session
from app.schemas.resume import ResumeBasicInfoResponse
from app.models.resume import ResumeBasicInfo
from app.core.config import SessionLocal
from app.utils.file import save_profile_image
from typing import Optional
from datetime import datetime
from app.models.portfolio import Portfolio
from app.models.project import Project
from app.models.award import Award
from app.models.education import Education
from app.schemas.project import ProjectResponse
from app.schemas.award import AwardResponse
from app.schemas.education import EducationResponse

router = APIRouter(prefix="/resumes", tags=["Resume"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/basic-info/", response_model=ResumeBasicInfoResponse)
def create_resume_basic_info(
    profile_image: Optional[UploadFile] = File(None),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    job_type: str = Form(...),
    school: str = Form(...),
    major: str = Form(...),
    grade: str = Form(...),
    period: str = Form(...),
    short_intro: str = Form(...),
    intro: str = Form(...),
    db: Session = Depends(get_db),
    # user_id: int = Depends(get_current_user) # 실제 서비스에서는 인증 필요
):
    # 임시 user_id (실제 서비스에서는 인증에서 받아옴)
    user_id = 1

    # 이메일 중복 체크 (회원 테이블과 연동 필요)
    # if db.query(User).filter(User.email == email).first():
    #     raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    image_path = None
    if profile_image:
        image_path = save_profile_image(profile_image)

    resume = ResumeBasicInfo(
        user_id=user_id,
        profile_image=image_path,
        name=name,
        email=email,
        phone=phone,
        job_type=job_type,
        school=school,
        major=major,
        grade=grade,
        period=period,
        short_intro=short_intro,
        intro=intro,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

@router.get("/{resume_id}/detail")
def get_resume_detail(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")
    portfolios = db.query(Portfolio).filter(Portfolio.resume_id == resume_id).all()
    projects = db.query(Project).filter(Project.portfolio_id.in_([p.id for p in portfolios])).all()
    awards = db.query(Award).filter(Award.resume_id == resume_id).all()
    educations = db.query(Education).filter(Education.resume_id == resume_id).all()
    return {
        "resume": resume,
        "portfolios": portfolios,
        "projects": projects,
        "awards": awards,
        "educations": educations
    } 