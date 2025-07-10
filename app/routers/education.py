from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.education import Education
from app.schemas.education import EducationCreate, EducationResponse
from app.core.config import SessionLocal
from typing import List

router = APIRouter(prefix="/educations", tags=["Education"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/",
    response_model=EducationResponse,
    summary="교육 등록",
    description="""
    이력서에 교육 이력을 등록합니다.\n
    - `resume_id`: 이력서 ID (필수)\n    - `institution`: 교육 기관명 (필수)\n    - `period`: 교육 기간 (필수, 예: 2023-01 ~ 2023-06)\n    - `name`: 교육명 (필수)\n
    **응답:** 등록된 교육 이력의 상세 정보 반환
    """,
    responses={
        200: {
            "description": "교육 등록 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "resume_id": 2,
                        "institution": "멋쟁이사자처럼 대학",
                        "period": "2023-01 ~ 2023-06",
                        "name": "AI 엔지니어링 부트캠프",
                        "created_at": "2023-06-30T12:00:00"
                    }
                }
            }
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"}
    }
)
def create_education(education: EducationCreate, db: Session = Depends(get_db)):
    db_education = Education(**education.dict())
    db.add(db_education)
    db.commit()
    db.refresh(db_education)
    return db_education 