from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.user import User, StudentProfile
from app.models.portfolio import Portfolio
from app.models.connect import ConnectRequest
from app.schemas.connect import ConnectRequestCreate, ConnectRequestResponse
from app.core.config import SessionLocal
from app.utils.slack import send_slack_message
from typing import List, Optional

router = APIRouter(prefix="/talents", tags=["Talent"])

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(
    "/",
    response_model=List[dict],
    summary="인재 탐색 및 검색",
    description="""
    전체 인재(수료생) 목록을 탐색하거나, 기술 스택/과정명으로 필터링하여 검색합니다.\n
    - 쿼리 파라미터 없이 호출 시 전체 인재 반환\n    - `tech_stack`: 검색할 기술 스택 (선택)\n    - `course_name`: 검색할 과정명 (선택)\n
    **응답:**\n    - `portfolio_id`: 포트폴리오 ID\n    - `student_user_id`: 학생 사용자 ID\n    - `student_email`: 학생 이메일\n    - `course_name`: 과정명\n    - `tech_stack`: 기술 스택\n    - `project_name`: 프로젝트명\n    - `project_intro`: 프로젝트 소개\n    - `is_representative`: 대표 포트폴리오 여부\n    - `project_image_url`: 대표 프로젝트 이미지 URL
    """,
    responses={
        200: {
            "description": "인재 탐색/검색 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "portfolio_id": 1,
                            "student_user_id": 1,
                            "student_email": "student1@example.com",
                            "course_name": "웹개발 과정",
                            "tech_stack": "React, Node.js, MongoDB",
                            "project_name": "쇼핑몰 웹사이트",
                            "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                            "is_representative": True,
                            "project_image_url": "/media/portfolio/1.png"
                        },
                        {
                            "portfolio_id": 2,
                            "student_user_id": 2,
                            "student_email": "student2@example.com",
                            "course_name": "AI 엔지니어 과정",
                            "tech_stack": "Python, TensorFlow",
                            "project_name": "AI 이미지 분류",
                            "project_intro": "딥러닝 기반 이미지 분류 프로젝트",
                            "is_representative": False,
                            "project_image_url": None
                        }
                    ]
                }
            }
        }
    }
)
def list_talents(
    tech_stack: Optional[str] = Query(None, description="검색할 기술 스택 (예: React, Python)"),
    course_name: Optional[str] = Query(None, description="검색할 과정명 (예: 웹개발 과정)"),
    db: Session = Depends(get_db),
):
    """
    조건에 맞는 인재(수료생)를 검색합니다.
    
    기술 스택과 과정명을 기준으로 필터링하여
    기업이 원하는 인재를 찾을 수 있도록 도와줍니다.
    """
    query = db.query(Portfolio, User, StudentProfile).join(User, Portfolio.resume_id == User.id).join(StudentProfile, StudentProfile.user_id == User.id)
    if tech_stack:
        query = query.filter(StudentProfile.tech_stack.contains(tech_stack))
    if course_name:
        query = query.filter(StudentProfile.course_name == course_name)
    results = query.all()
    # 간단한 dict 변환
    return [
        {
            "portfolio_id": p.id,
            "student_user_id": u.id,
            "student_email": u.email,
            "course_name": s.course_name,
            "tech_stack": s.tech_stack,
            "project_name": p.project_name,
            "project_intro": p.project_intro,
            "is_representative": p.is_representative,
            "project_image_url": p.image,  # 대표 프로젝트 이미지 URL 추가
        }
        for p, u, s in results
    ]

@router.post(
    "/connect-request",
    response_model=ConnectRequestResponse,
    summary="인재 연결 요청",
    description="""
    특정 인재(수료생)에게 채용/연결 요청을 보냅니다.\n
    - `company_user_id`: 기업 사용자 ID (필수)\n    - `student_user_id`: 학생 사용자 ID (필수)\n    - `portfolio_id`: 포트폴리오 ID (필수)\n    - `message`: 연결 요청 메시지 (선택)\n    - `position`: 채용 포지션 (선택)\n    - `job_description`: 직무 설명 (선택)\n    - `required_stack`: 필수 기술 스택 (선택)\n    - `career_level`: 희망 경력 수준 (선택)\n    - `employment_type`: 고용 수준 (선택)\n
    **응답:** 생성된 연결 요청의 상세 정보 반환
    """,
    responses={
        200: {
            "description": "연결 요청 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "company_user_id": 10,
                        "student_user_id": 1,
                        "portfolio_id": 1,
                        "message": "안녕하세요! 귀하의 포트폴리오를 보고 연락드립니다.",
                        "position": "프론트엔드 개발자",
                        "job_description": "React 기반 웹앱 개발",
                        "required_stack": "React, TypeScript",
                        "career_level": "신입~3년",
                        "employment_type": "정규직",
                        "created_at": "2024-07-01T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "중복 요청 또는 잘못된 데이터",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "이미 커넥트 요청이 존재합니다."
                    }
                }
            }
        },
        500: {"description": "서버 오류"}
    }
)
def create_connect_request(
    req: ConnectRequestCreate,
    db: Session = Depends(get_db),
):
    """
    특정 인재(수료생)에게 연결 요청을 보냅니다.
    
    기업이 관심 있는 인재에게 연결 요청을 보내며,
    중복 요청을 방지하고 Slack 알림을 통해 실시간으로 알림을 전송합니다.
    """
    # 중복 요청 방지
    exists = db.query(ConnectRequest).filter(
        ConnectRequest.company_user_id == req.company_user_id,
        ConnectRequest.student_user_id == req.student_user_id,
        ConnectRequest.portfolio_id == req.portfolio_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 커넥트 요청이 존재합니다.")
    connect = ConnectRequest(
        company_user_id=req.company_user_id,
        student_user_id=req.student_user_id,
        portfolio_id=req.portfolio_id,
        message=req.message,
        position=req.position,
        job_description=req.job_description,
        required_stack=req.required_stack,
        career_level=req.career_level,
        employment_type=req.employment_type
    )
    db.add(connect)
    db.commit()
    db.refresh(connect)
    # 슬랙 알림 전송
    if SLACK_WEBHOOK_URL:
        msg = f"[커넥트 요청] 기업ID: {req.company_user_id} → 수료생ID: {req.student_user_id} (포트폴리오ID: {req.portfolio_id})\n포지션: {req.position or '-'}\n직무설명: {req.job_description or '-'}\n필수스택: {req.required_stack or '-'}\n경력수준: {req.career_level or '-'}\n고용수준: {req.employment_type or '-'}\n메시지: {req.message or '-'}"
        send_slack_message(SLACK_WEBHOOK_URL, msg)
    return connect 