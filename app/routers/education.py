from fastapi import APIRouter, Depends, HTTPException, Path, Query, Form
from sqlalchemy.orm import Session
from app.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.core.config import get_db
from app.models.education import Education
from typing import List, Optional
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/educations", tags=["Education"])

@router.post("/", response_model=EducationResponse)
def create_education(
    resume_id: int = Form(..., description="이력서 ID"),
    institution: str = Form(..., description="교육 기관"),
    period: str = Form(..., description="교육 기간"),
    name: str = Form(..., description="교육명"),
    db: Session = Depends(get_db)
):
    """
    교육 이력을 생성합니다. (FormData 지원)
    """
    try:
        # 요청 데이터 로깅
        request_data = {
            "resume_id": resume_id,
            "institution": institution,
            "period": period,
            "name": name
        }
        logger.info(f"교육 이력 생성 요청 데이터: {request_data}")
        
        # 유효성 검사
        if resume_id <= 0:
            raise HTTPException(status_code=400, detail="이력서 ID는 0보다 커야 합니다")
        if not institution.strip():
            raise HTTPException(status_code=400, detail="교육 기관은 비어있을 수 없습니다")
        if not period.strip():
            raise HTTPException(status_code=400, detail="교육 기간은 비어있을 수 없습니다")
        if not name.strip():
            raise HTTPException(status_code=400, detail="교육명은 비어있을 수 없습니다")
        
        # 교육 이력 생성
        db_education = Education(
            resume_id=resume_id,
            institution=institution.strip(),
            period=period.strip(),
            name=name.strip(),
            created_at=datetime.utcnow()
        )
        
        db.add(db_education)
        db.commit()
        db.refresh(db_education)
        
        logger.info(f"교육 이력 생성 성공: ID {db_education.id}")
        return db_education
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"교육 이력 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"교육 이력 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/json", response_model=EducationResponse)
def create_education_json(
    education: EducationCreate,
    db: Session = Depends(get_db)
):
    """
    교육 이력을 생성합니다. (JSON 지원)
    """
    try:
        logger.info(f"교육 이력 생성 요청 데이터 (JSON): {education.dict()}")
        
        db_education = Education(**education.dict())
        db.add(db_education)
        db.commit()
        db.refresh(db_education)
        return db_education
        
    except Exception as e:
        logger.error(f"교육 이력 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"교육 이력 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/", response_model=List[EducationResponse])
def get_educations(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    resume_id: Optional[int] = Query(None, description="이력서 ID로 필터링"),
    db: Session = Depends(get_db)
):
    """
    교육 이력 목록을 조회합니다.
    """
    query = db.query(Education)
    
    if resume_id:
        query = query.filter(Education.resume_id == resume_id)
    
    educations = query.offset(skip).limit(limit).all()
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
    education_update: EducationUpdate,
    education_id: int = Path(..., description="교육 이력 ID"),
    db: Session = Depends(get_db)
):
    """
    교육 이력을 수정합니다.
    """
    db_education = db.query(Education).filter(Education.id == education_id).first()
    if not db_education:
        raise HTTPException(status_code=404, detail="교육 이력을 찾을 수 없습니다.")
    
    # 업데이트할 필드만 처리
    update_data = education_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
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