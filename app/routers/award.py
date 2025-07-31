from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.award import Award
from app.schemas.award import AwardCreate, AwardResponse
from app.core.config import SessionLocal
from typing import List
from app.models.resume import ResumeBasicInfo

router = APIRouter(prefix="/awards", tags=["Award"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/",
    response_model=AwardResponse,
    summary="수상 및 활동 등록",
    description="""
    이력서에 수상 및 활동(자격증명 등)을 등록합니다.\n
    - `user_id`: 사용자 ID (필수)\n    - `name`: 수상/자격증명 (필수)\n    - `date`: 취득일 (필수, 예: 2024-06)\n    - `organization`: 기관명 (필수)\n
    **응답:** 등록된 수상/활동의 상세 정보 반환
    """,
    responses={
        200: {
            "description": "수상 및 활동 등록 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "resume_id": 2,
                        "name": "정보처리기사",
                        "date": "2024-06",
                        "organization": "한국산업인력공단",
                        "created_at": "2024-06-30T12:00:00"
                    }
                }
            }
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"}
    }
)
def create_award(award: AwardCreate, db: Session = Depends(get_db)):
    # user_id로 resume_id 자동 조회 (ResumeBasicInfo의 id가 user_id 역할)
    resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == award.user_id).first()
    if not resume:
        raise HTTPException(status_code=400, detail="해당 사용자의 이력서가 존재하지 않습니다.")
    db_award = Award(
        resume_id=resume.id,
        name=award.name,
        date=award.date,
        organization=award.organization
    )
    db.add(db_award)
    db.commit()
    db.refresh(db_award)
    return db_award

@router.get(
    "/{user_id}",
    response_model=List[AwardResponse],
    summary="사용자별 수상 및 활동 조회",
    description="""
    특정 사용자의 모든 수상 및 활동 내역을 조회합니다.\n
    - `user_id`: 사용자 ID (필수)\n
    **응답:** 해당 사용자의 수상/활동 목록 반환
    """,
    responses={
        200: {
            "description": "수상 및 활동 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "resume_id": 2,
                            "name": "정보처리기사",
                            "date": "2024-06",
                            "organization": "한국산업인력공단",
                            "created_at": "2024-06-30T12:00:00"
                        },
                        {
                            "id": 2,
                            "resume_id": 2,
                            "name": "SQLD",
                            "date": "2024-05",
                            "organization": "한국데이터산업진흥원",
                            "created_at": "2024-05-15T10:30:00"
                        }
                    ]
                }
            }
        },
        404: {"description": "사용자를 찾을 수 없음"}
    }
)
def get_awards_by_user(user_id: int, db: Session = Depends(get_db)):
    # user_id로 resume_id 조회
    resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == user_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="해당 사용자의 이력서가 존재하지 않습니다.")
    
    # 해당 사용자의 모든 수상 내역 조회
    awards = db.query(Award).filter(Award.resume_id == resume.id).all()
    return awards 