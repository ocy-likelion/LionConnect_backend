from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.schemas.education import EducationCreate, EducationResponse
from app.core.config import get_db
from app.models.education import Education
from typing import List

router = APIRouter(prefix="/educations", tags=["Education"])

@router.post("/", response_model=EducationResponse)
def create_education(
    education: EducationCreate,
    db: Session = Depends(get_db)
):
    """
    교육 이력을 생성합니다.
    """
    db_education = Education(**education.dict())
    db.add(db_education)
    db.commit()
    db.refresh(db_education)
    return db_education

@router.get("/", response_model=List[EducationResponse])
def get_educations(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    교육 이력 목록을 조회합니다.
    """
    educations = db.query(Education).offset(skip).limit(limit).all()
    return educations

@router.get("/{education_id}", response_model=EducationResponse)
def get_education(
    education_id: int = Path(..., description="교육 이력 ID"),
    db: Session = Depends(get_db)
):
    """
    특정 교육 이력을 조회합니다.
    """
    education = db.query(Education).filter(Education.id == education_id).first()
    if not education:
        raise HTTPException(status_code=404, detail="교육 이력을 찾을 수 없습니다.")
    return education

@router.put("/{education_id}", response_model=EducationResponse)
def update_education(
    education_id: int = Path(..., description="교육 이력 ID"),
    education: EducationCreate = None,
    db: Session = Depends(get_db)
):
    """
    교육 이력을 수정합니다.
    """
    db_education = db.query(Education).filter(Education.id == education_id).first()
    if not db_education:
        raise HTTPException(status_code=404, detail="교육 이력을 찾을 수 없습니다.")
    
    for key, value in education.dict().items():
        setattr(db_education, key, value)
    
    db.commit()
    db.refresh(db_education)
    return db_education

@router.delete("/{education_id}")
def delete_education(
    education_id: int = Path(..., description="교육 이력 ID"),
    db: Session = Depends(get_db)
):
    """
    교육 이력을 삭제합니다.
    """
    education = db.query(Education).filter(Education.id == education_id).first()
    if not education:
        raise HTTPException(status_code=404, detail="교육 이력을 찾을 수 없습니다.")
    
    db.delete(education)
    db.commit()
    return {"message": "교육 이력이 삭제되었습니다."} 