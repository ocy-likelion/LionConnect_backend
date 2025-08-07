from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse, ProjectUpdate
from app.core.config import get_db
from app.models.project import Project
from typing import List, Optional
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Project"])

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    프로젝트를 생성합니다.
    
    필수 필드:
    - portfolio_id: 포트폴리오 ID
    - project_name: 프로젝트명
    - project_period: 프로젝트 기간
    - project_intro: 프로젝트 소개
    - description: 프로젝트 설명
    - role: 담당 역할
    - tech_stack: 기술 스택
    - user_id: 사용자 ID
    
    선택 필드:
    - github_url: GitHub URL
    """
    try:
        # 요청 데이터 로깅
        logger.info(f"프로젝트 생성 요청 데이터: {project.dict()}")
        
        # 프로젝트 생성
        db_project = Project(
            portfolio_id=project.portfolio_id,
            project_name=project.project_name,
            project_period=project.project_period,
            project_intro=project.project_intro,
            description=project.description,
            role=project.role,
            tech_stack=project.tech_stack,
            user_id=project.user_id,
            github_url=project.github_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        logger.info(f"생성할 프로젝트 객체: {db_project.__dict__}")
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        logger.info(f"프로젝트 생성 성공: ID {db_project.id}")
        return db_project
        
    except Exception as e:
        logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}")
        logger.error(f"요청 데이터: {project.dict() if project else 'None'}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/test", summary="프로젝트 생성 테스트")
def test_project_creation(
    project_data: dict,
    db: Session = Depends(get_db)
):
    """
    프로젝트 생성 테스트용 엔드포인트
    요청 데이터를 로깅하여 문제를 파악할 수 있습니다.
    """
    try:
        logger.info(f"테스트 요청 데이터: {project_data}")
        
        # 데이터 유효성 검사
        required_fields = ['portfolio_id', 'project_name', 'project_period', 'project_intro', 'description', 'role', 'tech_stack', 'user_id']
        missing_fields = []
        
        for field in required_fields:
            if field not in project_data or project_data[field] is None or project_data[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "error": "필수 필드 누락",
                "missing_fields": missing_fields,
                "received_data": project_data
            }
        
        # 타입 검사
        type_errors = []
        if not isinstance(project_data.get('portfolio_id'), int):
            type_errors.append("portfolio_id는 정수여야 합니다")
        if not isinstance(project_data.get('user_id'), int):
            type_errors.append("user_id는 정수여야 합니다")
        if not isinstance(project_data.get('project_name'), str):
            type_errors.append("project_name은 문자열이어야 합니다")
        
        if type_errors:
            return {
                "error": "타입 오류",
                "type_errors": type_errors,
                "received_data": project_data
            }
        
        return {
            "success": True,
            "message": "데이터 형식이 올바릅니다",
            "received_data": project_data
        }
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        return {
            "error": "테스트 중 오류 발생",
            "error_message": str(e),
            "received_data": project_data
        }

@router.get("/", response_model=ProjectListResponse)
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="사용자 ID로 필터링"),
    db: Session = Depends(get_db)
):
    """
    프로젝트 목록을 조회합니다.
    
    쿼리 파라미터:
    - skip: 건너뛸 개수
    - limit: 가져올 개수
    - user_id: 특정 사용자의 프로젝트만 조회 (선택)
    """
    query = db.query(Project)
    
    if user_id:
        query = query.filter(Project.user_id == user_id)
    
    projects = query.offset(skip).limit(limit).all()
    total = query.count()
    
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
    project_update: ProjectUpdate,
    project_id: int = Path(..., description="프로젝트 ID"),
    db: Session = Depends(get_db)
):
    """
    프로젝트를 수정합니다.
    
    업데이트할 필드만 전송하면 됩니다.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    # 업데이트할 필드만 처리
    update_data = project_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_project, key, value)
    
    db_project.updated_at = datetime.utcnow()
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