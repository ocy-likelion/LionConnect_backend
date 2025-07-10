from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.award import Award
from app.schemas.award import AwardCreate, AwardResponse
from app.core.config import SessionLocal
from typing import List

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
    - `resume_id`: 이력서 ID (필수)\n    - `name`: 수상/자격증명명 (필수)\n    - `date`: 취득일 (필수, 예: 2024-06)\n    - `organization`: 기관명 (필수)\n
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
    db_award = Award(**award.dict())
    db.add(db_award)
    db.commit()
    db.refresh(db_award)
    return db_award 