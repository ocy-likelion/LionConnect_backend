from fastapi import APIRouter, Depends, HTTPException, Path, Query, Form
from sqlalchemy.orm import Session
from app.schemas.award import AwardCreate, AwardResponse, AwardUpdate
from app.core.config import get_db
from app.models.award import Award
from typing import List, Optional
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/awards", tags=["Award"])

@router.post("/", response_model=AwardResponse)
def create_award(
    resume_id: int = Form(..., description="이력서 ID"),
    name: str = Form(..., description="수상/자격증명"),
    date: str = Form(..., description="취득일"),
    organization: str = Form(..., description="기관명"),
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 생성합니다. (FormData 지원)
    """
    try:
        # 요청 데이터 로깅
        request_data = {
            "resume_id": resume_id,
            "name": name,
            "date": date,
            "organization": organization
        }
        logger.info(f"수상/자격증 생성 요청 데이터: {request_data}")
        
        # 유효성 검사
        if resume_id <= 0:
            raise HTTPException(status_code=400, detail="이력서 ID는 0보다 커야 합니다")
        if not name.strip():
            raise HTTPException(status_code=400, detail="수상/자격증명은 비어있을 수 없습니다")
        if not date.strip():
            raise HTTPException(status_code=400, detail="취득일은 비어있을 수 없습니다")
        if not organization.strip():
            raise HTTPException(status_code=400, detail="기관명은 비어있을 수 없습니다")
        
        # 수상/자격증 생성
        db_award = Award(
            resume_id=resume_id,
            name=name.strip(),
            date=date.strip(),
            organization=organization.strip(),
            created_at=datetime.utcnow()
        )
        
        db.add(db_award)
        db.commit()
        db.refresh(db_award)
        
        logger.info(f"수상/자격증 생성 성공: ID {db_award.id}")
        return db_award
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수상/자격증 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"수상/자격증 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/json", response_model=AwardResponse)
def create_award_json(
    award: AwardCreate,
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 생성합니다. (JSON 지원)
    """
    try:
        logger.info(f"수상/자격증 생성 요청 데이터 (JSON): {award.dict()}")
        
        db_award = Award(**award.dict())
        db.add(db_award)
        db.commit()
        db.refresh(db_award)
        return db_award
        
    except Exception as e:
        logger.error(f"수상/자격증 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"수상/자격증 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/", response_model=List[AwardResponse])
def get_awards(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    resume_id: Optional[int] = Query(None, description="이력서 ID로 필터링"),
    db: Session = Depends(get_db)
):
    """
    수상 및 활동 목록을 조회합니다.
    """
    query = db.query(Award)
    
    if resume_id:
        query = query.filter(Award.resume_id == resume_id)
    
    awards = query.offset(skip).limit(limit).all()
    return awards

@router.get("/{award_id}", response_model=AwardResponse)
def get_award(
    award_id: int = Path(..., description="수상 및 활동 ID"),
    db: Session = Depends(get_db)
):
    """
    특정 수상 및 활동을 조회합니다.
    """
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="수상 및 활동을 찾을 수 없습니다.")
    return award

@router.put("/{award_id}", response_model=AwardResponse)
def update_award(
    award_update: AwardUpdate,
    award_id: int = Path(..., description="수상 및 활동 ID"),
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 수정합니다.
    """
    db_award = db.query(Award).filter(Award.id == award_id).first()
    if not db_award:
        raise HTTPException(status_code=404, detail="수상 및 활동을 찾을 수 없습니다.")
    
    # 업데이트할 필드만 처리
    update_data = award_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_award, key, value)
    
    db.commit()
    db.refresh(db_award)
    return db_award

@router.delete("/{award_id}")
def delete_award(
    award_id: int = Path(..., description="수상 및 활동 ID"),
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 삭제합니다.
    """
    award = db.query(Award).filter(Award.id == award_id).first()
    if not award:
        raise HTTPException(status_code=404, detail="수상 및 활동을 찾을 수 없습니다.")
    
    db.delete(award)
    db.commit()
    return {"message": "수상 및 활동이 삭제되었습니다."} 