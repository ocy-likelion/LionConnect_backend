from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioListResponse
from app.core.config import get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/portfolios", tags=["Portfolio"])

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 생성합니다.
    """
    db_portfolio = Portfolio(**portfolio.dict())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.get("/", response_model=PortfolioListResponse)
def get_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 목록을 조회합니다.
    """
    portfolios = db.query(Portfolio).offset(skip).limit(limit).all()
    total = db.query(Portfolio).count()
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
    portfolio_id: int = Path(..., description="포트폴리오 ID"),
    portfolio: PortfolioCreate = None,
    db: Session = Depends(get_db)
):
    """
    포트폴리오를 수정합니다.
    """
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    for key, value in portfolio.dict().items():
        setattr(db_portfolio, key, value)
    
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