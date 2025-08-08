from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.core.config import get_db
from app.models.user import User, UserTypeEnum, StudentProfile
from app.models.resume import ResumeBasicInfo
from app.models.portfolio import Portfolio
from app.models.project import Project
from app.models.award import Award
from app.models.education import Education

from pydantic import BaseModel, Field, validator


router = APIRouter(prefix="/admin/bulk", tags=["AdminBulk"])


# ======================
# Pydantic 요청 스키마
# ======================

class BulkPortfolio(BaseModel):
    project_name: str
    project_intro: str
    project_period: str
    role: str
    is_representative: bool = False
    image: Optional[str] = None
    project_url: Optional[str] = None


class BulkProject(BaseModel):
    project_name: str
    project_period: str
    project_intro: str
    description: str
    role: str
    tech_stack: str
    github_url: Optional[str] = None


class BulkAward(BaseModel):
    name: str
    date: str
    organization: str


class BulkEducation(BaseModel):
    institution: str
    period: str
    name: str


class BulkUser(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    name: str
    course_name: str
    course_generation: str
    tech_stack: str


class BulkResume(BaseModel):
    profile_image: Optional[str] = None
    name: str
    email: str
    phone: str
    job_type: str
    school: str
    major: str
    grade: str
    period: str
    short_intro: str
    intro: str
    age: Optional[int] = None


class BulkTalent(BaseModel):
    user: BulkUser
    resume: BulkResume
    portfolios: Optional[List[BulkPortfolio]] = None
    projects: Optional[List[BulkProject]] = None
    awards: Optional[List[BulkAward]] = None
    educations: Optional[List[BulkEducation]] = None


class BulkTalentsRequest(BaseModel):
    talents: List[BulkTalent]


# ======================
# 유틸
# ======================

def _ensure_student_user(db: Session, payload: BulkUser) -> User:
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        return user
    user = User(
        email=payload.email,
        name=payload.name,
        user_type=UserTypeEnum.student,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    user.set_password(payload.password)
    db.add(user)
    db.flush()  # user.id 생성

    profile = StudentProfile(
        user_id=user.id,
        course_name=payload.course_name,
        course_generation=payload.course_generation,
        tech_stack=payload.tech_stack,
    )
    db.add(profile)
    return user


# ======================
# 엔드포인트
# ======================

@router.post("/talents", summary="관리자 전용: 인재 데이터 대량 등록 (JSON)")
def bulk_create_talents(
    body: BulkTalentsRequest,
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    """
    관리자 전용 대량 등록 API. 기존 라우터/엔드포인트는 전혀 변경하지 않습니다.

    - 입력: JSON 하나에 여러 명의 인재를 포함
    - 동작: 각 인재에 대해 User → Resume → Portfolio/Project/Award/Education 순으로 생성
    - 결과: 성공/실패 내역을 개별로 반환 (부분 성공 허용)
    - 보안: 환경변수 ADMIN_API_KEY가 설정되어 있으면 요청 헤더 `X-Admin-Api-Key` 검사
    """

    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env:
        if not x_admin_api_key or x_admin_api_key != admin_key_env:
            raise HTTPException(status_code=401, detail="Unauthorized: invalid admin api key")

    results: List[Dict[str, Any]] = []

    for idx, talent in enumerate(body.talents):
        try:
            # 사용자 확보
            user = _ensure_student_user(db, talent.user)

            # 이력서 생성
            resume = ResumeBasicInfo(
                profile_image=talent.resume.profile_image,
                name=talent.resume.name,
                email=talent.resume.email,
                phone=talent.resume.phone,
                job_type=talent.resume.job_type,
                school=talent.resume.school,
                major=talent.resume.major,
                grade=talent.resume.grade,
                period=talent.resume.period,
                short_intro=talent.resume.short_intro,
                intro=talent.resume.intro,
                age=talent.resume.age,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(resume)
            db.flush()  # resume.id 생성

            # 포트폴리오들
            created_portfolios = 0
            for p in talent.portfolios or []:
                db.add(
                    Portfolio(
                        user_id=user.id,
                        is_representative=p.is_representative,
                        image=p.image,
                        project_url=p.project_url,
                        project_name=p.project_name,
                        project_intro=p.project_intro,
                        project_period=p.project_period,
                        role=p.role,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                created_portfolios += 1

            # 프로젝트들
            created_projects = 0
            for pr in talent.projects or []:
                db.add(
                    Project(
                        user_id=user.id,
                        project_name=pr.project_name,
                        project_period=pr.project_period,
                        project_intro=pr.project_intro,
                        description=pr.description,
                        role=pr.role,
                        tech_stack=pr.tech_stack,
                        github_url=pr.github_url,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                created_projects += 1

            # 수상/자격증
            created_awards = 0
            for a in talent.awards or []:
                db.add(
                    Award(
                        resume_id=resume.id,
                        name=a.name,
                        date=a.date,
                        organization=a.organization,
                        created_at=datetime.utcnow(),
                    )
                )
                created_awards += 1

            # 교육
            created_educations = 0
            for e in talent.educations or []:
                db.add(
                    Education(
                        resume_id=resume.id,
                        institution=e.institution,
                        period=e.period,
                        name=e.name,
                        created_at=datetime.utcnow(),
                    )
                )
                created_educations += 1

            db.commit()

            results.append(
                {
                    "index": idx,
                    "email": user.email,
                    "user_id": user.id,
                    "resume_id": resume.id,
                    "portfolios": created_portfolios,
                    "projects": created_projects,
                    "awards": created_awards,
                    "educations": created_educations,
                    "status": "success",
                }
            )
        except Exception as e:
            db.rollback()
            results.append(
                {
                    "index": idx,
                    "email": getattr(talent.user, "email", None),
                    "status": "failed",
                    "error": str(e),
                }
            )

    success_count = sum(1 for r in results if r.get("status") == "success")
    fail_count = len(results) - success_count
    return {
        "total": len(results),
        "success": success_count,
        "failed": fail_count,
        "results": results,
    }


