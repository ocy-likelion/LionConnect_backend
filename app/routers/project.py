from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse
from app.core.config import get_db
from app.models.project import Project
from typing import List, Optional

router = APIRouter(prefix="/projects", tags=["Project"])

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    프로젝트를 생성합니다.
    """
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=ProjectListResponse)
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    프로젝트 목록을 조회합니다.
    """
    projects = db.query(Project).offset(skip).limit(limit).all()
    total = db.query(Project).count()
    return ProjectListResponse(projects=projects, total=total)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int = Path(..., description="프로젝트 ID"),
    db: Session = Depends(get_db)
):
    """
    특정 프로젝트를 조회합니다.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int = Path(..., description="프로젝트 ID"),
    project: ProjectCreate = None,
    db: Session = Depends(get_db)
):
    """
    프로젝트를 수정합니다.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    for key, value in project.dict().items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}")
def delete_project(
    project_id: int = Path(..., description="프로젝트 ID"),
    db: Session = Depends(get_db)
):
    """
    프로젝트를 삭제합니다.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    db.delete(project)
    db.commit()
    return {"message": "프로젝트가 삭제되었습니다."} 