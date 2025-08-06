from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.schemas.award import AwardCreate, AwardResponse
from app.core.config import get_db
from app.models.award import Award
from typing import List

router = APIRouter(prefix="/awards", tags=["Award"])

@router.post("/", response_model=AwardResponse)
def create_award(
    award: AwardCreate,
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 생성합니다.
    """
    db_award = Award(**award.dict())
    db.add(db_award)
    db.commit()
    db.refresh(db_award)
    return db_award

@router.get("/", response_model=List[AwardResponse])
def get_awards(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    수상 및 활동 목록을 조회합니다.
    """
    awards = db.query(Award).offset(skip).limit(limit).all()
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
    award_id: int = Path(..., description="수상 및 활동 ID"),
    award: AwardCreate = None,
    db: Session = Depends(get_db)
):
    """
    수상 및 활동을 수정합니다.
    """
    db_award = db.query(Award).filter(Award.id == award_id).first()
    if not db_award:
        raise HTTPException(status_code=404, detail="수상 및 활동을 찾을 수 없습니다.")
    
    for key, value in award.dict().items():
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