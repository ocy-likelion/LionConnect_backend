from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.config import get_db, SLACK_WEBHOOK_URL
from app.models.connect import ConnectRequest
from app.models.user import User, StudentProfile
from app.models.portfolio import Portfolio
from app.models.resume import ResumeBasicInfo
from app.schemas.connect import ConnectRequestCreate, ConnectRequestResponse
from app.utils.slack import send_slack_message

router = APIRouter(prefix="/connect", tags=["커넥트"])

@router.post(
    "/request",
    response_model=ConnectRequestResponse,
    status_code=201,
    summary="🦁 커넥트 요청 생성 (개선된 버전)",
    description="""
    ## 기업담당자가 수료생에게 커넥트 요청을 보냅니다.
    
    ### 📋 필수 정보
    - **user_id**: 수료생 사용자 ID
    - **company_representative_name**: 기업담당자 이름
    - **company_representative_email**: 기업담당자 이메일
    - **company_representative_phone**: 기업담당자 전화번호
    
    ### 🔄 자동 처리
    - **portfolio_id**: 수료생의 대표 포트폴리오를 자동으로 찾아서 설정
    - **company_user_id**: 로그인하지 않은 사용자는 null로 설정
    
    ### 📝 선택 정보
    - **company_name**: 기업명
    - **message**: 커넥트 요청 메시지
    - **position**: 채용 포지션
    - **job_description**: 직무 설명
    - **required_stack**: 필수 기술 스택
    - **career_level**: 희망 경력 수준
    - **employment_type**: 고용 형태
    
    ### 📈 개선사항
    - 로그인 없이도 사용 가능
    - portfolio_id 자동 설정
    - 더 간단한 API 사용법
    """,
    responses={
        201: {
            "description": "✅ 커넥트 요청 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "company_user_id": None,
                        "user_id": 1,
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
            "description": "❌ 잘못된 데이터 또는 중복 요청",
            "content": {
                "application/json": {
                    "examples": {
                        "duplicate_request": {
                            "summary": "중복 요청",
                            "value": {"detail": "이미 커넥트 요청이 존재합니다."}
                        },
                        "missing_fields": {
                            "summary": "필수 필드 누락",
                            "value": {"detail": "기업담당자 기본 정보가 누락되었습니다."}
                        }
                    }
                }
            }
        },
        404: {
            "description": "❌ 수료생을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "수료생의 이력서를 찾을 수 없습니다."}
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
    ## 커넥트 요청 생성 (개선된 버전)
    
    ### 주요 변경사항:
    - user_id만 입력받음
    - portfolio_id 자동 설정
    - company_user_id는 로그인하지 않은 사용자는 null
    - resume_basic_info 테이블에서 수료생 정보 조회
    """
    try:
        # 입력 데이터 검증
        if not req.company_representative_name or not req.company_representative_email or not req.company_representative_phone:
            raise HTTPException(status_code=400, detail="기업담당자 기본 정보가 누락되었습니다.")
        
        if not req.user_id:
            raise HTTPException(status_code=400, detail="수료생 정보가 누락되었습니다.")
        
        # 수료생 존재 여부 확인 (resume_basic_info 테이블에서)
        student_resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.user_id == req.user_id).first()
        if not student_resume:
            raise HTTPException(status_code=404, detail="수료생의 이력서를 찾을 수 없습니다.")
        
        # 수료생의 대표 포트폴리오 자동 찾기 (없어도 OK)
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == req.user_id,
            Portfolio.is_representative == True
        ).first()
        
        # 대표 포트폴리오가 없으면 첫 번째 포트폴리오 사용
        if not portfolio:
            portfolio = db.query(Portfolio).filter(
                Portfolio.user_id == req.user_id
            ).first()
        
        # 포트폴리오가 없어도 커넥트 요청은 가능 (portfolio_id는 null로 설정)
        portfolio_id = portfolio.id if portfolio else None
        
        # 중복 요청 방지 (같은 기업담당자가 같은 수료생에게 보낸 요청)
        exists = db.query(ConnectRequest).filter(
            ConnectRequest.company_representative_email == req.company_representative_email,
            ConnectRequest.user_id == req.user_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="이미 커넥트 요청이 존재합니다.")
        
        # 커넥트 요청 생성 (company_user_id는 null, portfolio_id는 자동 설정)
        connect = ConnectRequest(
            company_user_id=None,  # 로그인하지 않은 사용자
            user_id=req.user_id,
            portfolio_id=portfolio_id,  # 포트폴리오가 없으면 null
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
                # 수료생 정보 조회 (resume_basic_info에서)
                student_resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.user_id == req.user_id).first()
                
                slack_message = f"""
🦁 *새로운 커넥트 요청이 도착했습니다!*

*기업담당자 정보:*
• 이름: {req.company_representative_name}
• 이메일: {req.company_representative_email}
• 전화번호: {req.company_representative_phone}
• 기업명: {req.company_name or '미입력'}

*수료생 정보:*
• 이름: {student_resume.name if student_resume else '미입력'}
• 이메일: {student_resume.email if student_resume else '미입력'}
• 전화번호: {student_resume.phone if student_resume else '미입력'}
• 희망 직무: {student_resume.job_type if student_resume else '미입력'}
• 학교: {student_resume.school if student_resume else '미입력'}
• 전공: {student_resume.major if student_resume else '미입력'}

*포트폴리오 정보:*
• 프로젝트명: {portfolio.project_name if portfolio else '포트폴리오 없음'}
• 프로젝트 소개: {portfolio.project_intro if portfolio else '포트폴리오 없음'}

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
                print(f"Slack 알림 전송 실패 (요청은 성공): {str(e)}")
        
        return connect
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"커넥트 요청 생성 중 오류 발생: {str(e)}")
        print(f"요청 데이터: {req}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.get(
    "/requests/{user_id}",
    response_model=List[ConnectRequestResponse],
    summary="수료생의 커넥트 요청 목록 조회",
    description="특정 수료생이 받은 모든 커넥트 요청을 조회합니다."
)
def get_connect_requests_by_student(
    user_id: int,
    db: Session = Depends(get_db),
):
    requests = db.query(ConnectRequest).filter(
        ConnectRequest.user_id == user_id
    ).all()
    return requests

@router.get(
    "/users",
    summary="🦁 커넥트 요청 가능한 사용자 목록",
    description="커넥트 요청을 받을 수 있는 사용자 목록을 조회합니다."
)
def get_available_users(db: Session = Depends(get_db)):
    """
    커넥트 요청을 받을 수 있는 사용자 목록을 반환합니다.
    """
    # resume_basic_info 테이블에서 수료생 정보 조회
    resumes = db.query(ResumeBasicInfo).all()
    return [
        {
            "id": resume.user_id,
            "name": resume.name,
            "email": resume.email,
            "phone": resume.phone,
            "job_type": resume.job_type,
            "school": resume.school,
            "major": resume.major,
            "created_at": resume.created_at
        }
        for resume in resumes
    ] 