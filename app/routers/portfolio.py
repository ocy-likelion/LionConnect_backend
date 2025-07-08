from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.schemas.portfolio import PortfolioResponse, PortfolioUpdate
from app.models.portfolio import Portfolio
from app.core.config import SessionLocal
from app.utils.file import save_profile_image
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/portfolios", tags=["Portfolio"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    resume_id: int = Form(...),
    is_representative: Optional[bool] = Form(False),
    image: Optional[UploadFile] = File(None),
    project_url: Optional[str] = Form(None),
    project_name: str = Form(...),
    project_intro: str = Form(...),
    project_period: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    image_path = None
    if image:
        image_path = save_profile_image(image)

    # 대표 포트폴리오로 설정 시, 기존 대표 해제
    if is_representative:
        db.query(Portfolio).filter(Portfolio.resume_id == resume_id).update({"is_representative": False})

    portfolio = Portfolio(
        resume_id=resume_id,
        is_representative=is_representative,
        image=image_path,
        project_url=project_url,
        project_name=project_name,
        project_intro=project_intro,
        project_period=project_period,
        role=role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.get("/", response_model=List[PortfolioResponse])
def get_portfolios(resume_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Portfolio).filter(Portfolio.resume_id == resume_id).all()

@router.patch("/{portfolio_id}/representative", response_model=PortfolioResponse)
def set_representative_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    # 같은 이력서의 다른 포트폴리오 대표 해제
    db.query(Portfolio).filter(Portfolio.resume_id == portfolio.resume_id).update({"is_representative": False})
    portfolio.is_representative = True
    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    db.delete(portfolio)
    db.commit()
    return

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    is_representative: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    project_url: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
    project_intro: Optional[str] = Form(None),
    project_period: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

    # 대표 포트폴리오로 설정 시, 기존 대표 해제
    if is_representative is not None:
        if is_representative:
            db.query(Portfolio).filter(Portfolio.resume_id == portfolio.resume_id).update({"is_representative": False})
        portfolio.is_representative = is_representative

    if image:
        portfolio.image = save_profile_image(image)
    if project_url is not None:
        portfolio.project_url = project_url
    if project_name is not None:
        portfolio.project_name = project_name
    if project_intro is not None:
        portfolio.project_intro = project_intro
    if project_period is not None:
        portfolio.project_period = project_period
    if role is not None:
        portfolio.role = role
    portfolio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(portfolio)
    return portfolio 