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

@router.get("/", response_model=List[dict])
def list_talents(
    tech_stack: Optional[str] = Query(None),
    course_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
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

@router.post("/connect-request", response_model=ConnectRequestResponse)
def create_connect_request(
    req: ConnectRequestCreate,
    db: Session = Depends(get_db),
):
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