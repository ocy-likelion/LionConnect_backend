from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User, StudentProfile
from app.models.portfolio import Portfolio
from app.models.connect import ConnectRequest
from app.schemas.connect import ConnectRequestCreate, ConnectRequestResponse
from app.core.config import SessionLocal
from app.utils.slack import send_slack_message
from typing import List

router = APIRouter(prefix="/connect", tags=["Connect"])

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/request",
    response_model=ConnectRequestResponse,
    summary="커넥트 요청 생성",
    description="""
    기업담당자가 수료생에게 커넥트 요청을 보냅니다.
    
    **필수 정보:**
    - `company_representative_name`: 기업담당자 이름
    - `company_representative_email`: 기업담당자 이메일
    - `company_representative_phone`: 기업담당자 전화번호
    - `student_user_id`: 수료생 사용자 ID
    - `portfolio_id`: 포트폴리오 ID
    
    **선택 정보:**
    - `company_name`: 기업명
    - `message`: 커넥트 요청 메시지
    - `position`: 채용 포지션
    - `job_description`: 직무 설명
    - `required_stack`: 필수 기술 스택
    - `career_level`: 희망 경력 수준
    - `employment_type`: 고용 형태
    
    **응답:** 생성된 커넥트 요청의 상세 정보와 Slack 알림 전송
    """,
    responses={
        201: {
            "description": "커넥트 요청 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "company_user_id": 10,
                        "student_user_id": 1,
                        "portfolio_id": 1,
                        "company_representative_name": "김기업",
                        "company_representative_email": "kim@company.com",
                        "company_representative_phone": "010-1234-5678",
                        "company_name": "테크컴퍼니",
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
            "description": "잘못된 데이터 또는 중복 요청",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "이미 커넥트 요청이 존재합니다."
                    }
                }
            }
        },
        404: {
            "description": "사용자 또는 포트폴리오를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "수료생을 찾을 수 없습니다."
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
    기업담당자가 수료생에게 커넥트 요청을 보냅니다.
    
    기업담당자의 기본 정보와 함께 커넥트 요청을 생성하며,
    중복 요청을 방지하고 Slack 알림을 통해 실시간으로 알림을 전송합니다.
    """
    try:
        # 입력 데이터 검증
        if not req.company_representative_name or not req.company_representative_email or not req.company_representative_phone:
            raise HTTPException(status_code=400, detail="기업담당자 기본 정보가 누락되었습니다.")
        
        if not req.student_user_id or not req.portfolio_id:
            raise HTTPException(status_code=400, detail="수료생 정보가 누락되었습니다.")
        
        # 포트폴리오 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == req.portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
        
        # 수료생 존재 여부 확인
        student_user = db.query(User).filter(User.id == req.student_user_id).first()
        if not student_user:
            raise HTTPException(status_code=404, detail="수료생을 찾을 수 없습니다.")
        
        # 중복 요청 방지 (같은 기업담당자가 같은 수료생에게 보낸 요청)
        exists = db.query(ConnectRequest).filter(
            ConnectRequest.company_representative_email == req.company_representative_email,
            ConnectRequest.student_user_id == req.student_user_id,
            ConnectRequest.portfolio_id == req.portfolio_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="이미 커넥트 요청이 존재합니다.")
        
        # 커넥트 요청 생성
        connect = ConnectRequest(
            company_user_id=req.company_user_id,
            student_user_id=req.student_user_id,
            portfolio_id=req.portfolio_id,
            company_representative_name=req.company_representative_name,
            company_representative_email=req.company_representative_email,
            company_representative_phone=req.company_representative_phone,
            company_name=req.company_name,
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
        
        # Slack 알림 전송
        if SLACK_WEBHOOK_URL:
            try:
                # 수료생 정보 조회
                student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == req.student_user_id).first()
                
                slack_message = f"""
🦁 *새로운 커넥트 요청이 도착했습니다!*

*기업담당자 정보:*
• 이름: {req.company_representative_name}
• 이메일: {req.company_representative_email}
• 전화번호: {req.company_representative_phone}
• 기업명: {req.company_name or '미입력'}

*수료생 정보:*
• 이름: {student_user.name or '미입력'}
• 이메일: {student_user.email}
• 과정명: {student_profile.course_name if student_profile else '미입력'}
• 기술스택: {student_profile.tech_stack if student_profile else '미입력'}

*포트폴리오 정보:*
• 프로젝트명: {portfolio.project_name}
• 프로젝트 소개: {portfolio.project_intro}

*채용 정보:*
• 포지션: {req.position or '미입력'}
• 직무 설명: {req.job_description or '미입력'}
• 필수 기술스택: {req.required_stack or '미입력'}
• 경력 수준: {req.career_level or '미입력'}
• 고용 형태: {req.employment_type or '미입력'}

*메시지:*
{req.message or '메시지 없음'}

---
요청 시간: {connect.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
                send_slack_message(SLACK_WEBHOOK_URL, slack_message)
            except Exception as e:
                # Slack 알림 실패는 로그만 남기고 전체 요청은 성공으로 처리
                print(f"Slack 알림 전송 실패 (요청은 성공): {str(e)}")
        
        return connect
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"커넥트 요청 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="커넥트 요청 생성 중 오류가 발생했습니다.")

@router.get(
    "/requests/{student_user_id}",
    response_model=List[ConnectRequestResponse],
    summary="수료생의 커넥트 요청 목록 조회",
    description="특정 수료생이 받은 모든 커넥트 요청을 조회합니다."
)
def get_connect_requests_by_student(
    student_user_id: int,
    db: Session = Depends(get_db),
):
    """특정 수료생이 받은 모든 커넥트 요청을 조회합니다."""
    requests = db.query(ConnectRequest).filter(
        ConnectRequest.student_user_id == student_user_id
    ).order_by(ConnectRequest.created_at.desc()).all()
    
    return requests 