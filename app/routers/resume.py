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

@router.post(
    "/basic-info/", 
    response_model=ResumeBasicInfoResponse,
    summary="이력서 기본 정보 생성",
    description="""
    ## 이력서의 기본 정보를 생성합니다.
    
    ### 기능 설명
    - 사용자의 기본 정보 (이름, 연락처, 학력 등)를 저장
    - 프로필 이미지 업로드 지원
    - 이력서 작성의 첫 단계
    
    ### 요청 데이터 (multipart/form-data)
    - `profile_image`: 프로필 이미지 파일 (선택사항)
    - `name`: 이름 (필수)
    - `email`: 이메일 주소 (필수)
    - `phone`: 전화번호 (필수)
    - `job_type`: 희망 직무 (필수)
    - `school`: 학교명 (필수)
    - `major`: 전공 (필수)
    - `grade`: 학년 (필수)
    - `period`: 재학 기간 (필수)
    - `short_intro`: 간단 소개 (필수)
    - `intro`: 상세 소개 (필수)
    
    ### 지원 파일 형식
    - 이미지: JPG, PNG, GIF (최대 5MB)
    
    ### 응답 데이터
    - `id`: 이력서 ID
    - `user_id`: 사용자 ID
    - `profile_image`: 프로필 이미지 경로
    - `name`: 이름
    - `email`: 이메일
    - `phone`: 전화번호
    - `job_type`: 희망 직무
    - `school`: 학교명
    - `major`: 전공
    - `grade`: 학년
    - `period`: 재학 기간
    - `short_intro`: 간단 소개
    - `intro`: 상세 소개
    - `created_at`: 생성 시간
    - `updated_at`: 수정 시간
    
    ### 에러 응답
    - `400 Bad Request`: 필수 필드 누락 또는 파일 형식 오류
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "이력서 기본 정보 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "profile_image": "/media/profile/user1.jpg",
                        "name": "홍길동",
                        "email": "hong@example.com",
                        "phone": "010-1234-5678",
                        "job_type": "프론트엔드 개발자",
                        "school": "서울대학교",
                        "major": "컴퓨터공학과",
                        "grade": "4학년",
                        "period": "2020-2024",
                        "short_intro": "웹 개발에 열정을 가진 학생입니다.",
                        "intro": "프론트엔드 개발에 관심이 많아 React, Vue.js 등을 학습하고 있습니다...",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00"
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "필수 필드가 누락되었습니다."
                    }
                }
            }
        }
    }
)
def create_resume_basic_info(
    profile_image: Optional[UploadFile] = File(
        None, 
        description="프로필 이미지 파일 (JPG, PNG, GIF, 최대 5MB)"
    ),
    name: str = Form(..., description="이름"),
    email: str = Form(..., description="이메일 주소"),
    phone: str = Form(..., description="전화번호"),
    job_type: str = Form(..., description="희망 직무"),
    school: str = Form(..., description="학교명"),
    major: str = Form(..., description="전공"),
    grade: str = Form(..., description="학년"),
    period: str = Form(..., description="재학 기간"),
    short_intro: str = Form(..., description="간단 소개"),
    intro: str = Form(..., description="상세 소개"),
    db: Session = Depends(get_db),
    # user_id: int = Depends(get_current_user) # 실제 서비스에서는 인증 필요
):
    """
    이력서의 기본 정보를 생성합니다.
    
    사용자의 개인정보, 학력, 소개 등을 포함한 이력서의 기본 정보를 저장합니다.
    프로필 이미지 업로드도 지원합니다.
    """
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

@router.get(
    "/{resume_id}/detail",
    summary="이력서 상세 정보 조회",
    description="""
    ## 특정 이력서의 모든 정보를 조회합니다.
    
    ### 기능 설명
    - 이력서 기본 정보
    - 포트폴리오 목록
    - 프로젝트 목록
    - 수상 내역
    - 교육 내역
    
    ### 경로 파라미터
    - `resume_id`: 조회할 이력서의 ID (정수)
    
    ### 응답 데이터
    - `resume`: 이력서 기본 정보
    - `portfolios`: 포트폴리오 목록
    - `projects`: 프로젝트 목록
    - `awards`: 수상 내역
    - `educations`: 교육 내역
    
    ### 에러 응답
    - `404 Not Found`: 이력서를 찾을 수 없음
    """,
    responses={
        200: {
            "description": "이력서 상세 정보 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "resume": {
                            "id": 1,
                            "user_id": 1,
                            "name": "홍길동",
                            "email": "hong@example.com",
                            "job_type": "프론트엔드 개발자",
                            "school": "서울대학교",
                            "major": "컴퓨터공학과"
                        },
                        "portfolios": [
                            {
                                "id": 1,
                                "title": "웹 포트폴리오",
                                "description": "React로 만든 포트폴리오"
                            }
                        ],
                        "projects": [
                            {
                                "id": 1,
                                "title": "쇼핑몰 프로젝트",
                                "description": "React + Node.js 쇼핑몰"
                            }
                        ],
                        "awards": [
                            {
                                "id": 1,
                                "title": "우수상",
                                "organization": "대학 프로그래밍 대회"
                            }
                        ],
                        "educations": [
                            {
                                "id": 1,
                                "institution": "서울대학교",
                                "degree": "컴퓨터공학 학사"
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "이력서를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "이력서를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def get_resume_detail(
    resume_id: int = Path(..., description="조회할 이력서의 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 이력서의 모든 상세 정보를 조회합니다.
    
    이력서 기본 정보와 함께 관련된 포트폴리오, 프로젝트, 
    수상 내역, 교육 내역을 모두 포함하여 반환합니다.
    """
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