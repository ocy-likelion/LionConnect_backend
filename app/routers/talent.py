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
    summary="인재 검색",
    description="""
    ## 조건에 맞는 인재(수료생)를 검색합니다.
    
    ### 기능 설명
    - 기술 스택과 과정명으로 인재 필터링
    - 포트폴리오 정보와 함께 인재 정보 제공
    - 기업의 인재 발굴을 위한 검색 기능
    
    ### 쿼리 파라미터
    - `tech_stack`: 검색할 기술 스택 (선택사항)
    - `course_name`: 검색할 과정명 (선택사항)
    
    ### 응답 데이터
    - `portfolio_id`: 포트폴리오 ID
    - `student_user_id`: 학생 사용자 ID
    - `student_email`: 학생 이메일
    - `course_name`: 과정명
    - `tech_stack`: 기술 스택
    - `project_name`: 프로젝트명
    - `project_intro`: 프로젝트 소개
    - `is_representative`: 대표 포트폴리오 여부
    
    ### 예시
    ```
    GET /talents?tech_stack=React&course_name=웹개발
    GET /talents?tech_stack=Python
    GET /talents?course_name=데이터분석
    ```
    """,
    responses={
        200: {
            "description": "인재 검색 성공",
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
                            "is_representative": True
                        },
                        {
                            "portfolio_id": 2,
                            "student_user_id": 2,
                            "student_email": "student2@example.com",
                            "course_name": "웹개발 과정",
                            "tech_stack": "Vue.js, Python, Django",
                            "project_name": "포트폴리오 웹사이트",
                            "project_intro": "개인 포트폴리오 웹사이트",
                            "is_representative": False
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
        }
        for p, u, s in results
    ]

@router.post(
    "/connect-request", 
    response_model=ConnectRequestResponse,
    summary="인재 연결 요청",
    description="""
    ## 특정 인재(수료생)에게 연결 요청을 보냅니다.
    
    ### 기능 설명
    - 기업이 관심 있는 인재에게 연결 요청
    - 중복 요청 방지 (같은 기업-학생-포트폴리오 조합)
    - Slack 알림을 통한 실시간 요청 알림
    - 메시지와 함께 연결 요청 전송
    
    ### 요청 데이터
    - `company_user_id`: 기업 사용자 ID (필수)
    - `student_user_id`: 학생 사용자 ID (필수)
    - `portfolio_id`: 포트폴리오 ID (필수)
    - `message`: 연결 요청 메시지 (선택사항)
    
    ### 응답 데이터
    - `id`: 연결 요청 ID
    - `company_user_id`: 기업 사용자 ID
    - `student_user_id`: 학생 사용자 ID
    - `portfolio_id`: 포트폴리오 ID
    - `message`: 연결 요청 메시지
    - `created_at`: 요청 생성 시간
    
    ### 에러 응답
    - `400 Bad Request`: 중복 요청 또는 잘못된 데이터
    - `500 Internal Server Error`: 서버 내부 오류
    
    ### Slack 알림
    연결 요청이 생성되면 Slack으로 실시간 알림이 전송됩니다.
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
                        "message": "안녕하세요! 귀하의 포트폴리오를 보고 관심이 생겨서 연락드립니다. 채용 관련하여 상담 가능하신가요?",
                        "created_at": "2024-01-01T00:00:00"
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
        }
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
        message=req.message
    )
    db.add(connect)
    db.commit()
    db.refresh(connect)
    # 슬랙 알림 전송
    if SLACK_WEBHOOK_URL:
        msg = f"[커넥트 요청] 기업ID: {req.company_user_id} → 수료생ID: {req.student_user_id} (포트폴리오ID: {req.portfolio_id})\n메시지: {req.message or '-'}"
        send_slack_message(SLACK_WEBHOOK_URL, msg)
    return connect 