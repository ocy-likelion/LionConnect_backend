from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, Path
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

@router.post(
    "/", 
    response_model=ProjectResponse,
    summary="프로젝트 생성",
    description="""
    ## 새로운 프로젝트를 생성합니다.
    
    ### 기능 설명
    - 포트폴리오에 연결된 개별 프로젝트 정보 저장
    - 프로젝트의 상세 정보와 기술 스택 관리
    - 포트폴리오 내에서 프로젝트 세분화
    
    ### 요청 데이터 (multipart/form-data)
    - `portfolio_id`: 연결할 포트폴리오 ID (필수)
    - `project_name`: 프로젝트명 (필수)
    - `project_period`: 프로젝트 기간 (필수)
    - `project_intro`: 프로젝트 소개 (필수)
    - `description`: 프로젝트 상세 설명 (필수)
    - `role`: 프로젝트에서의 역할 (필수)
    - `tech_stack`: 사용 기술 스택 (필수)
    
    ### 응답 데이터
    - `id`: 프로젝트 ID
    - `portfolio_id`: 연결된 포트폴리오 ID
    - `project_name`: 프로젝트명
    - `project_period`: 프로젝트 기간
    - `project_intro`: 프로젝트 소개
    - `description`: 프로젝트 상세 설명
    - `role`: 프로젝트에서의 역할
    - `tech_stack`: 사용 기술 스택
    - `created_at`: 생성 시간
    - `updated_at`: 수정 시간
    
    ### 에러 응답
    - `400 Bad Request`: 필수 필드 누락
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "프로젝트 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "portfolio_id": 1,
                        "project_name": "쇼핑몰 결제 시스템",
                        "project_period": "2024.01 - 2024.02",
                        "project_intro": "온라인 쇼핑몰의 결제 시스템 개발",
                        "description": "사용자가 상품을 선택하고 결제할 수 있는 시스템을 개발했습니다. 결제 보안과 사용자 경험을 중점으로 설계했습니다.",
                        "role": "백엔드 개발",
                        "tech_stack": "Node.js, Express, MongoDB, JWT",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00"
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "필수 필드가 누락되었습니다."
                    }
                }
            }
        }
    }
)
def create_project(
    portfolio_id: int = Form(..., description="연결할 포트폴리오 ID"),
    project_name: str = Form(..., description="프로젝트명"),
    project_period: str = Form(..., description="프로젝트 기간"),
    project_intro: str = Form(..., description="프로젝트 소개"),
    description: str = Form(..., description="프로젝트 상세 설명"),
    role: str = Form(..., description="프로젝트에서의 역할"),
    tech_stack: str = Form(..., description="사용 기술 스택"),
    db: Session = Depends(get_db),
):
    """
    새로운 프로젝트를 생성합니다.
    
    포트폴리오에 연결된 개별 프로젝트의 상세 정보를 저장합니다.
    프로젝트의 기술 스택과 역할 정보를 포함합니다.
    """
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

@router.get(
    "/", 
    response_model=List[ProjectResponse],
    summary="프로젝트 목록 조회",
    description="""
    ## 특정 포트폴리오의 프로젝트 목록을 조회합니다.
    
    ### 기능 설명
    - 포트폴리오 ID로 연결된 모든 프로젝트 조회
    - 프로젝트의 기본 정보 목록 반환
    
    ### 쿼리 파라미터
    - `portfolio_id`: 조회할 포트폴리오 ID (필수)
    
    ### 응답 데이터
    - 프로젝트 객체 배열
    
    ### 예시
    ```
    GET /projects?portfolio_id=1
    ```
    """,
    responses={
        200: {
            "description": "프로젝트 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "portfolio_id": 1,
                            "project_name": "쇼핑몰 결제 시스템",
                            "project_period": "2024.01 - 2024.02",
                            "project_intro": "온라인 쇼핑몰의 결제 시스템 개발",
                            "description": "사용자가 상품을 선택하고 결제할 수 있는 시스템을 개발했습니다.",
                            "role": "백엔드 개발",
                            "tech_stack": "Node.js, Express, MongoDB, JWT"
                        },
                        {
                            "id": 2,
                            "portfolio_id": 1,
                            "project_name": "관리자 대시보드",
                            "project_period": "2024.02 - 2024.03",
                            "project_intro": "쇼핑몰 관리자용 대시보드 개발",
                            "description": "상품 관리, 주문 관리, 통계 확인이 가능한 관리자 페이지를 개발했습니다.",
                            "role": "프론트엔드 개발",
                            "tech_stack": "React, TypeScript, Chart.js"
                        }
                    ]
                }
            }
        }
    }
)
def get_projects(
    portfolio_id: int = Query(..., description="조회할 포트폴리오 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 포트폴리오의 프로젝트 목록을 조회합니다.
    """
    return db.query(Project).filter(Project.portfolio_id == portfolio_id).all()

@router.put(
    "/{project_id}", 
    response_model=ProjectResponse,
    summary="프로젝트 수정",
    description="""
    ## 특정 프로젝트의 정보를 수정합니다.
    
    ### 기능 설명
    - 프로젝트의 모든 필드 수정 가능
    - 부분 업데이트 지원 (변경된 필드만 전송)
    - 프로젝트 상세 정보 업데이트
    
    ### 경로 파라미터
    - `project_id`: 수정할 프로젝트 ID
    
    ### 요청 데이터 (multipart/form-data)
    - `project_name`: 프로젝트명 (선택사항)
    - `project_period`: 프로젝트 기간 (선택사항)
    - `project_intro`: 프로젝트 소개 (선택사항)
    - `description`: 프로젝트 상세 설명 (선택사항)
    - `role`: 프로젝트에서의 역할 (선택사항)
    - `tech_stack`: 사용 기술 스택 (선택사항)
    
    ### 응답 데이터
    - 업데이트된 프로젝트 정보
    
    ### 에러 응답
    - `404 Not Found`: 프로젝트를 찾을 수 없음
    - `400 Bad Request`: 잘못된 요청 데이터
    """,
    responses={
        200: {
            "description": "프로젝트 수정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "portfolio_id": 1,
                        "project_name": "쇼핑몰 결제 시스템 v2",
                        "project_period": "2024.01 - 2024.03",
                        "project_intro": "온라인 쇼핑몰의 결제 시스템 개발 (업데이트됨)",
                        "description": "사용자가 상품을 선택하고 결제할 수 있는 시스템을 개발했습니다. 결제 보안과 사용자 경험을 중점으로 설계했습니다. 추가로 모바일 결제 기능을 구현했습니다.",
                        "role": "풀스택 개발",
                        "tech_stack": "Node.js, Express, MongoDB, JWT, React Native",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-02T00:00:00"
                    }
                }
            }
        },
        404: {
            "description": "프로젝트를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "프로젝트를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def update_project(
    project_id: int = Path(..., description="수정할 프로젝트 ID"),
    project_name: Optional[str] = Form(None, description="프로젝트명"),
    project_period: Optional[str] = Form(None, description="프로젝트 기간"),
    project_intro: Optional[str] = Form(None, description="프로젝트 소개"),
    description: Optional[str] = Form(None, description="프로젝트 상세 설명"),
    role: Optional[str] = Form(None, description="프로젝트에서의 역할"),
    tech_stack: Optional[str] = Form(None, description="사용 기술 스택"),
    db: Session = Depends(get_db),
):
    """
    특정 프로젝트의 정보를 수정합니다.
    
    전송된 필드만 업데이트되며, 프로젝트의 모든 정보를 수정할 수 있습니다.
    """
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

@router.delete(
    "/{project_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="프로젝트 삭제",
    description="""
    ## 특정 프로젝트를 삭제합니다.
    
    ### 기능 설명
    - 프로젝트와 관련된 모든 데이터 삭제
    - 삭제된 프로젝트는 복구 불가
    
    ### 경로 파라미터
    - `project_id`: 삭제할 프로젝트 ID
    
    ### 응답
    - `204 No Content`: 삭제 성공 (응답 본문 없음)
    
    ### 에러 응답
    - `404 Not Found`: 프로젝트를 찾을 수 없음
    """,
    responses={
        204: {
            "description": "프로젝트 삭제 성공"
        },
        404: {
            "description": "프로젝트를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "프로젝트를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def delete_project(
    project_id: int = Path(..., description="삭제할 프로젝트 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 프로젝트를 삭제합니다.
    
    프로젝트와 관련된 모든 데이터가 영구적으로 삭제됩니다.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    db.delete(project)
    db.commit()
    return 