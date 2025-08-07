from fastapi import APIRouter, Depends, HTTPException, Path, Query, Form, File
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
    portfolio_id: int = Form(..., description="포트폴리오 ID"),
    project_name: str = Form(..., description="프로젝트명"),
    project_period: str = Form(..., description="프로젝트 기간"),
    project_intro: str = Form(..., description="프로젝트 소개"),
    description: str = Form(..., description="프로젝트 설명"),
    role: str = Form(..., description="담당 역할"),
    tech_stack: str = Form(..., description="기술 스택"),
    user_id: int = Form(..., description="사용자 ID"),
    github_url: Optional[str] = Form(None, description="GitHub URL"),
    db: Session = Depends(get_db)
):
    """
    프로젝트를 생성합니다. (FormData 지원)
    
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
    
    중복 등록 허용: 같은 사용자가 같은 이름의 프로젝트를 여러 개 등록할 수 있습니다.
    """
    try:
        # 요청 데이터 로깅
        request_data = {
            "portfolio_id": portfolio_id,
            "project_name": project_name,
            "project_period": project_period,
            "project_intro": project_intro,
            "description": description,
            "role": role,
            "tech_stack": tech_stack,
            "user_id": user_id,
            "github_url": github_url
        }
        logger.info(f"프로젝트 생성 요청 데이터: {request_data}")
        
        # 1. 기본 유효성 검사
        if portfolio_id <= 0:
            raise HTTPException(status_code=400, detail="포트폴리오 ID는 0보다 커야 합니다")
        if user_id <= 0:
            raise HTTPException(status_code=400, detail="사용자 ID는 0보다 커야 합니다")
        if not project_name or not project_name.strip():
            raise HTTPException(status_code=400, detail="프로젝트명은 비어있을 수 없습니다")
        if not project_period or not project_period.strip():
            raise HTTPException(status_code=400, detail="프로젝트 기간은 비어있을 수 없습니다")
        if not project_intro or not project_intro.strip():
            raise HTTPException(status_code=400, detail="프로젝트 소개는 비어있을 수 없습니다")
        if not description or not description.strip():
            raise HTTPException(status_code=400, detail="프로젝트 설명은 비어있을 수 없습니다")
        if not role or not role.strip():
            raise HTTPException(status_code=400, detail="담당 역할은 비어있을 수 없습니다")
        if not tech_stack or not tech_stack.strip():
            raise HTTPException(status_code=400, detail="기술 스택은 비어있을 수 없습니다")
        
        # 2. 포트폴리오 존재 여부 확인
        from app.models.portfolio import Portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"포트폴리오 ID {portfolio_id}를 찾을 수 없습니다")
        
        # 3. 사용자 존재 여부 확인
        from app.models.resume import ResumeBasicInfo
        user = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"사용자 ID {user_id}를 찾을 수 없습니다")
        
        # 4. 프로젝트 생성 (중복 허용)
        db_project = Project(
            portfolio_id=portfolio_id,
            project_name=project_name.strip(),
            project_period=project_period.strip(),
            project_intro=project_intro.strip(),
            description=description.strip(),
            role=role.strip(),
            tech_stack=tech_stack.strip(),
            user_id=user_id,
            github_url=github_url.strip() if github_url and github_url.strip() else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        logger.info(f"생성할 프로젝트 객체: {db_project.__dict__}")
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        logger.info(f"프로젝트 생성 성공: ID {db_project.id}")
        return db_project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}")
        logger.error(f"요청 데이터: {request_data}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/json", response_model=ProjectResponse)
def create_project_json(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    프로젝트를 생성합니다. (JSON 지원)
    
    기존 JSON 방식의 API를 유지합니다.
    """
    try:
        # 요청 데이터 로깅
        logger.info(f"프로젝트 생성 요청 데이터 (JSON): {project.dict()}")
        
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
    portfolio_id: int = Form(..., description="포트폴리오 ID"),
    project_name: str = Form(..., description="프로젝트명"),
    project_period: str = Form(..., description="프로젝트 기간"),
    project_intro: str = Form(..., description="프로젝트 소개"),
    description: str = Form(..., description="프로젝트 설명"),
    role: str = Form(..., description="담당 역할"),
    tech_stack: str = Form(..., description="기술 스택"),
    user_id: int = Form(..., description="사용자 ID"),
    github_url: Optional[str] = Form(None, description="GitHub URL"),
    db: Session = Depends(get_db)
):
    """
    프로젝트 생성 요청을 테스트합니다.
    실제로 프로젝트를 생성하지 않고 요청 데이터만 검증합니다.
    """
    try:
        # 요청 데이터 수집
        request_data = {
            "portfolio_id": portfolio_id,
            "project_name": project_name,
            "project_period": project_period,
            "project_intro": project_intro,
            "description": description,
            "role": role,
            "tech_stack": tech_stack,
            "user_id": user_id,
            "github_url": github_url
        }
        
        logger.info(f"테스트 요청 데이터: {request_data}")
        
        # 데이터 타입 검증
        validation_results = {
            "portfolio_id": {
                "value": portfolio_id,
                "type": type(portfolio_id).__name__,
                "valid": isinstance(portfolio_id, int) and portfolio_id > 0
            },
            "project_name": {
                "value": project_name,
                "type": type(project_name).__name__,
                "valid": isinstance(project_name, str) and project_name.strip() != ""
            },
            "project_period": {
                "value": project_period,
                "type": type(project_period).__name__,
                "valid": isinstance(project_period, str) and project_period.strip() != ""
            },
            "project_intro": {
                "value": project_intro,
                "type": type(project_intro).__name__,
                "valid": isinstance(project_intro, str) and project_intro.strip() != ""
            },
            "description": {
                "value": description,
                "type": type(description).__name__,
                "valid": isinstance(description, str) and description.strip() != ""
            },
            "role": {
                "value": role,
                "type": type(role).__name__,
                "valid": isinstance(role, str) and role.strip() != ""
            },
            "tech_stack": {
                "value": tech_stack,
                "type": type(tech_stack).__name__,
                "valid": isinstance(tech_stack, str) and tech_stack.strip() != ""
            },
            "user_id": {
                "value": user_id,
                "type": type(user_id).__name__,
                "valid": isinstance(user_id, int) and user_id > 0
            },
            "github_url": {
                "value": github_url,
                "type": type(github_url).__name__ if github_url else "None",
                "valid": github_url is None or (isinstance(github_url, str) and github_url.strip() != "")
            }
        }
        
        # 포트폴리오 존재 여부 확인
        from app.models.portfolio import Portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        portfolio_exists = portfolio is not None
        
        # 사용자 존재 여부 확인
        from app.models.resume import ResumeBasicInfo
        user = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == user_id).first()
        user_exists = user is not None
        
        # 기존 프로젝트 개수 확인
        existing_projects = db.query(Project).filter(
            Project.user_id == user_id,
            Project.project_name == project_name.strip()
        ).count()
        
        return {
            "message": "프로젝트 생성 테스트 완료",
            "request_data": request_data,
            "validation_results": validation_results,
            "database_checks": {
                "portfolio_exists": portfolio_exists,
                "user_exists": user_exists,
                "existing_same_name_projects": existing_projects
            },
            "all_valid": all(field["valid"] for field in validation_results.values()) and portfolio_exists and user_exists
        }
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        return {
            "error": str(e),
            "message": "테스트 중 오류가 발생했습니다"
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