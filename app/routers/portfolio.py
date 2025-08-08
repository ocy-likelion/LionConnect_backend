from fastapi import APIRouter, Depends, HTTPException, Path, Query, Form
from sqlalchemy.orm import Session
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioListResponse, PortfolioUpdate
from app.core.config import get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from typing import List, Optional
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolios", tags=["Portfolio"])

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    user_id: int = Form(..., description="사용자 ID"),
    project_name: str = Form(..., description="프로젝트명"),
    project_intro: str = Form(..., description="프로젝트 소개"),
    project_period: str = Form(..., description="프로젝트 기간"),
    role: str = Form(..., description="담당 역할"),
    is_representative: bool = Form(False, description="대표 포트폴리오 여부"),
    image: Optional[str] = Form(None, description="포트폴리오 이미지"),
    project_url: Optional[str] = Form(None, description="프로젝트 URL"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 생성합니다. (FormData 지원)
    """
    try:
        # 요청 데이터 로깅
        request_data = {
            "user_id": user_id,
            "project_name": project_name,
            "project_intro": project_intro,
            "project_period": project_period,
            "role": role,
            "is_representative": is_representative,
            "image": image,
            "project_url": project_url
        }
        logger.info(f"포트폴리오 생성 요청 데이터: {request_data}")
        
        # 유효성 검사
        if user_id <= 0:
            raise HTTPException(status_code=400, detail="사용자 ID는 0보다 커야 합니다")
        if not project_name.strip():
            raise HTTPException(status_code=400, detail="프로젝트명은 비어있을 수 없습니다")
        if not project_intro.strip():
            raise HTTPException(status_code=400, detail="프로젝트 소개는 비어있을 수 없습니다")
        if not project_period.strip():
            raise HTTPException(status_code=400, detail="프로젝트 기간은 비어있을 수 없습니다")
        if not role.strip():
            raise HTTPException(status_code=400, detail="담당 역할은 비어있을 수 없습니다")
        
        # 사용자 존재 여부 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"사용자 ID {user_id}를 찾을 수 없습니다")
        
        # 포트폴리오 생성
        db_portfolio = Portfolio(
            user_id=user_id,
            project_name=project_name.strip(),
            project_intro=project_intro.strip(),
            project_period=project_period.strip(),
            role=role.strip(),
            is_representative=is_representative,
            image=image.strip() if image else None,
            project_url=project_url.strip() if project_url else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        
        logger.info(f"포트폴리오 생성 성공: ID {db_portfolio.id}")
        return db_portfolio
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트폴리오 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"포트폴리오 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/json", response_model=PortfolioResponse)
def create_portfolio_json(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 생성합니다. (JSON 지원)
    """
    try:
        logger.info(f"포트폴리오 생성 요청 데이터 (JSON): {portfolio.dict()}")
        
        db_portfolio = Portfolio(**portfolio.dict())
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio
        
    except Exception as e:
        logger.error(f"포트폴리오 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"포트폴리오 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/", response_model=PortfolioListResponse)
def get_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="사용자 ID로 필터링"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 목록을 조회합니다.
    """
    query = db.query(Portfolio)
    
    if user_id:
        query = query.filter(Portfolio.user_id == user_id)
    
    portfolios = query.offset(skip).limit(limit).all()
    total = query.count()
    return PortfolioListResponse(portfolios=portfolios, total=total)

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int = Path(..., description="포트폴리오 ID"),
    db: Session = Depends(get_db)
):
    """
    특정 포트폴리오를 조회합니다.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_update: PortfolioUpdate,
    portfolio_id: int = Path(..., description="포트폴리오 ID"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 수정합니다.
    """
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    # 업데이트할 필드만 처리
    update_data = portfolio_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_portfolio, key, value)
    
    db_portfolio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int = Path(..., description="포트폴리오 ID"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 삭제합니다.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    db.delete(portfolio)
    db.commit()
    return {"message": "포트폴리오가 삭제되었습니다."} 