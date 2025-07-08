from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate
from app.models.project import Project
from app.core.config import SessionLocal
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Project"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProjectResponse)
def create_project(
    portfolio_id: int = Form(...),
    project_name: str = Form(...),
    project_period: str = Form(...),
    project_intro: str = Form(...),
    description: str = Form(...),
    role: str = Form(...),
    tech_stack: str = Form(...),
    db: Session = Depends(get_db),
):
    project = Project(
        portfolio_id=portfolio_id,
        project_name=project_name,
        project_period=project_period,
        project_intro=project_intro,
        description=description,
        role=role,
        tech_stack=tech_stack,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=List[ProjectResponse])
def get_projects(portfolio_id: int, db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.portfolio_id == portfolio_id).all()

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_name: Optional[str] = Form(None),
    project_period: Optional[str] = Form(None),
    project_intro: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    tech_stack: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if project_name is not None:
        project.project_name = project_name
    if project_period is not None:
        project.project_period = project_period
    if project_intro is not None:
        project.project_intro = project_intro
    if description is not None:
        project.description = description
    if role is not None:
        project.role = role
    if tech_stack is not None:
        project.tech_stack = tech_stack
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    db.delete(project)
    db.commit()
    return 