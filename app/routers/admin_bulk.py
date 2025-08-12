from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re
import os

from app.core.config import get_db
from app.models.user import User, UserTypeEnum, StudentProfile
from app.models.resume import ResumeBasicInfo
from app.models.portfolio import Portfolio
from app.models.project import Project
from app.models.award import Award
from app.models.education import Education

from pydantic import BaseModel, Field, validator
from app.utils.storage import upload_image


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


# ===============
# Admin 단일 리소스용 Bulk 스키마 (기존 라우터 필수키 포함)
# ===============

class AdminPortfolioItem(BulkPortfolio):
    user_id: int


class AdminProjectItem(BulkProject):
    user_id: int


class AdminAwardItem(BulkAward):
    resume_id: int


class AdminEducationItem(BulkEducation):
    resume_id: int


class BulkItems[T](BaseModel):  # type: ignore[type-arg]
    items: List[T]


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


def _create_talents(db: Session, body: BulkTalentsRequest) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for idx, talent in enumerate(body.talents):
        try:
            user = _ensure_student_user(db, talent.user)

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
            db.flush()

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

    return _create_talents(db, body)


@router.post("/upload", summary="관리자 전용: 이미지 다중 업로드(Supabase)")
def admin_upload_images(
    files: list[UploadFile] = File(..., description="이미지 파일들"),
    folder: str = "misc",
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    """
    여러 이미지를 업로드하고 public URL 목록을 반환합니다.
    반환된 URL을 `/admin/bulk/talents`의 image 필드에 사용하세요.
    """
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid admin api key")

    urls: list[str] = []
    for f in files:
        urls.append(upload_image(f, folder=folder))
    return {"count": len(urls), "urls": urls}


@router.post("/talents-form", summary="관리자 전용: 인재 데이터+이미지 한 번에 (multipart/form-data)")
def bulk_create_talents_form(
    data: str = Form(..., description="BulkTalentsRequest JSON 문자열"),
    files: list[UploadFile] = File(None, description="이미지 파일들(선택)"),
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid admin api key")

    try:
        body = BulkTalentsRequest.model_validate_json(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"data(JSON) 파싱 실패: {str(e)}")

    # 파일명을 규칙으로 매핑: profile_{i}.*, t{i}_p{j}.*
    name_map = {f.filename: f for f in (files or []) if f and f.filename}
    profile_re = re.compile(r"^profile_(\d+)\.")
    portfolio_re = re.compile(r"^t(\d+)_p(\d+)\.")

    # 업로드 후 URL을 JSON에 주입
    for fname, file in name_map.items():
        m = profile_re.match(fname)
        if m:
            i = int(m.group(1))
            url = upload_image(file, folder="profile")
            if 0 <= i < len(body.talents):
                body.talents[i].resume.profile_image = url
            continue
        m = portfolio_re.match(fname)
        if m:
            i, j = int(m.group(1)), int(m.group(2))
            url = upload_image(file, folder="portfolio")
            if 0 <= i < len(body.talents):
                portfolios = body.talents[i].portfolios or []
                if 0 <= j < len(portfolios):
                    portfolios[j].image = url

    return _create_talents(db, body)


# =============================
# 기존 라우터의 관리자 버전 (간단 Bulk)
# =============================

@router.post("/portfolios", summary="관리자: 포트폴리오 다건 생성(JSON)")
def admin_bulk_portfolios(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized")

    items: List[Dict[str, Any]] = body.get("items", [])
    results: List[Dict[str, Any]] = []
    for idx, p in enumerate(items):
        try:
            db.add(
                Portfolio(
                    user_id=p["user_id"],
                    is_representative=bool(p.get("is_representative", False)),
                    image=p.get("image"),
                    project_url=p.get("project_url"),
                    project_name=p["project_name"].strip(),
                    project_intro=p["project_intro"].strip(),
                    project_period=p["project_period"].strip(),
                    role=p["role"].strip(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            db.commit()
            results.append({"index": idx, "status": "success"})
        except Exception as e:
            db.rollback()
            results.append({"index": idx, "status": "failed", "error": str(e)})
    return {"total": len(items), "results": results}


@router.post("/projects", summary="관리자: 프로젝트 다건 생성(JSON)")
def admin_bulk_projects(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized")

    items: List[Dict[str, Any]] = body.get("items", [])
    results: List[Dict[str, Any]] = []
    for idx, pr in enumerate(items):
        try:
            db.add(
                Project(
                    user_id=pr["user_id"],
                    project_name=pr["project_name"].strip(),
                    project_period=pr["project_period"].strip(),
                    project_intro=pr["project_intro"].strip(),
                    description=pr["description"].strip(),
                    role=pr["role"].strip(),
                    tech_stack=pr["tech_stack"].strip(),
                    github_url=(pr.get("github_url") or None),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            db.commit()
            results.append({"index": idx, "status": "success"})
        except Exception as e:
            db.rollback()
            results.append({"index": idx, "status": "failed", "error": str(e)})
    return {"total": len(items), "results": results}


@router.post("/awards", summary="관리자: 수상/자격증 다건 생성(JSON)")
def admin_bulk_awards(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized")

    items: List[Dict[str, Any]] = body.get("items", [])
    results: List[Dict[str, Any]] = []
    for idx, a in enumerate(items):
        try:
            db.add(
                Award(
                    resume_id=a["resume_id"],
                    name=a["name"].strip(),
                    date=a["date"].strip(),
                    organization=a["organization"].strip(),
                    created_at=datetime.utcnow(),
                )
            )
            db.commit()
            results.append({"index": idx, "status": "success"})
        except Exception as e:
            db.rollback()
            results.append({"index": idx, "status": "failed", "error": str(e)})
    return {"total": len(items), "results": results}


@router.post("/educations", summary="관리자: 교육 이력 다건 생성(JSON)")
def admin_bulk_educations(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(None, convert_underscores=False),
):
    admin_key_env = os.getenv("ADMIN_API_KEY")
    if admin_key_env and x_admin_api_key != admin_key_env:
        raise HTTPException(status_code=401, detail="Unauthorized")

    items: List[Dict[str, Any]] = body.get("items", [])
    results: List[Dict[str, Any]] = []
    for idx, e in enumerate(items):
        try:
            db.add(
                Education(
                    resume_id=e["resume_id"],
                    institution=e["institution"].strip(),
                    period=e["period"].strip(),
                    name=e["name"].strip(),
                    created_at=datetime.utcnow(),
                )
            )
            db.commit()
            results.append({"index": idx, "status": "success"})
        except Exception as ex:
            db.rollback()
            results.append({"index": idx, "status": "failed", "error": str(ex)})
    return {"total": len(items), "results": results}


