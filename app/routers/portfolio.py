from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status, Path
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

@router.post(
    "/", 
    response_model=PortfolioResponse,
    summary="포트폴리오 생성",
    description="""
    ## 새로운 포트폴리오를 생성합니다.
    
    ### 기능 설명
    - 프로젝트 포트폴리오 정보를 저장
    - 프로젝트 이미지 업로드 지원
    - 대표 포트폴리오 설정 가능
    - 이력서와 연결된 포트폴리오 관리
    
    ### 요청 데이터 (multipart/form-data)
    - `resume_id`: 연결할 이력서 ID (필수)
    - `is_representative`: 대표 포트폴리오 여부 (기본값: false)
    - `image`: 프로젝트 이미지 파일 (선택사항)
    - `project_url`: 프로젝트 URL (선택사항)
    - `project_name`: 프로젝트명 (필수)
    - `project_intro`: 프로젝트 소개 (필수)
    - `project_period`: 프로젝트 기간 (필수)
    - `role`: 프로젝트에서의 역할 (필수)
    
    ### 지원 파일 형식
    - 이미지: JPG, PNG, GIF (최대 5MB)
    
    ### 응답 데이터
    - `id`: 포트폴리오 ID
    - `resume_id`: 연결된 이력서 ID
    - `is_representative`: 대표 포트폴리오 여부
    - `image`: 프로젝트 이미지 경로
    - `project_url`: 프로젝트 URL
    - `project_name`: 프로젝트명
    - `project_intro`: 프로젝트 소개
    - `project_period`: 프로젝트 기간
    - `role`: 프로젝트에서의 역할
    - `created_at`: 생성 시간
    - `updated_at`: 수정 시간
    
    ### 에러 응답
    - `400 Bad Request`: 필수 필드 누락 또는 파일 형식 오류
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "포트폴리오 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "resume_id": 1,
                        "is_representative": True,
                        "image": "/media/profile/project1.jpg",
                        "project_url": "https://github.com/user/project",
                        "project_name": "쇼핑몰 웹사이트",
                        "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                        "project_period": "2024.01 - 2024.03",
                        "role": "프론트엔드 개발",
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
def create_portfolio(
    resume_id: int = Form(..., description="연결할 이력서 ID"),
    is_representative: Optional[bool] = Form(False, description="대표 포트폴리오 여부"),
    image: Optional[UploadFile] = File(None, description="프로젝트 이미지 파일"),
    project_url: Optional[str] = Form(None, description="프로젝트 URL"),
    project_name: str = Form(..., description="프로젝트명"),
    project_intro: str = Form(..., description="프로젝트 소개"),
    project_period: str = Form(..., description="프로젝트 기간"),
    role: str = Form(..., description="프로젝트에서의 역할"),
    db: Session = Depends(get_db),
):
    """
    새로운 포트폴리오를 생성합니다.
    
    프로젝트 정보와 이미지를 포함한 포트폴리오를 생성하며,
    대표 포트폴리오로 설정할 수 있습니다.
    """
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

@router.get(
    "/", 
    response_model=List[PortfolioResponse],
    summary="포트폴리오 목록 조회",
    description="""
    ## 특정 이력서의 포트폴리오 목록을 조회합니다.
    
    ### 기능 설명
    - 이력서 ID로 연결된 모든 포트폴리오 조회
    - 대표 포트폴리오 포함 전체 목록 반환
    
    ### 쿼리 파라미터
    - `resume_id`: 조회할 이력서 ID (필수)
    
    ### 응답 데이터
    - 포트폴리오 객체 배열
    
    ### 예시
    ```
    GET /portfolios?resume_id=1
    ```
    """,
    responses={
        200: {
            "description": "포트폴리오 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "resume_id": 1,
                            "is_representative": True,
                            "project_name": "쇼핑몰 웹사이트",
                            "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                            "project_period": "2024.01 - 2024.03",
                            "role": "프론트엔드 개발"
                        },
                        {
                            "id": 2,
                            "resume_id": 1,
                            "is_representative": False,
                            "project_name": "포트폴리오 웹사이트",
                            "project_intro": "개인 포트폴리오 웹사이트",
                            "project_period": "2024.02 - 2024.02",
                            "role": "풀스택 개발"
                        }
                    ]
                }
            }
        }
    }
)
def get_portfolios(
    resume_id: int = Query(..., description="조회할 이력서 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 이력서의 포트폴리오 목록을 조회합니다.
    """
    return db.query(Portfolio).filter(Portfolio.resume_id == resume_id).all()

@router.patch(
    "/{portfolio_id}/representative", 
    response_model=PortfolioResponse,
    summary="대표 포트폴리오 설정",
    description="""
    ## 특정 포트폴리오를 대표 포트폴리오로 설정합니다.
    
    ### 기능 설명
    - 선택한 포트폴리오를 대표 포트폴리오로 설정
    - 같은 이력서의 다른 포트폴리오는 자동으로 대표 해제
    - 한 이력서당 하나의 대표 포트폴리오만 가능
    
    ### 경로 파라미터
    - `portfolio_id`: 대표로 설정할 포트폴리오 ID
    
    ### 응답 데이터
    - 업데이트된 포트폴리오 정보
    
    ### 에러 응답
    - `404 Not Found`: 포트폴리오를 찾을 수 없음
    """,
    responses={
        200: {
            "description": "대표 포트폴리오 설정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "resume_id": 1,
                        "is_representative": True,
                        "project_name": "쇼핑몰 웹사이트",
                        "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                        "project_period": "2024.01 - 2024.03",
                        "role": "프론트엔드 개발"
                    }
                }
            }
        },
        404: {
            "description": "포트폴리오를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "포트폴리오를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def set_representative_portfolio(
    portfolio_id: int = Path(..., description="대표로 설정할 포트폴리오 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 포트폴리오를 대표 포트폴리오로 설정합니다.
    
    같은 이력서의 다른 포트폴리오는 자동으로 대표 해제됩니다.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    # 같은 이력서의 다른 포트폴리오 대표 해제
    db.query(Portfolio).filter(Portfolio.resume_id == portfolio.resume_id).update({"is_representative": False})
    portfolio.is_representative = True
    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.delete(
    "/{portfolio_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="포트폴리오 삭제",
    description="""
    ## 특정 포트폴리오를 삭제합니다.
    
    ### 기능 설명
    - 포트폴리오와 관련된 모든 데이터 삭제
    - 삭제된 포트폴리오는 복구 불가
    
    ### 경로 파라미터
    - `portfolio_id`: 삭제할 포트폴리오 ID
    
    ### 응답
    - `204 No Content`: 삭제 성공 (응답 본문 없음)
    
    ### 에러 응답
    - `404 Not Found`: 포트폴리오를 찾을 수 없음
    """,
    responses={
        204: {
            "description": "포트폴리오 삭제 성공"
        },
        404: {
            "description": "포트폴리오를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "포트폴리오를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def delete_portfolio(
    portfolio_id: int = Path(..., description="삭제할 포트폴리오 ID"), 
    db: Session = Depends(get_db)
):
    """
    특정 포트폴리오를 삭제합니다.
    
    포트폴리오와 관련된 모든 데이터가 영구적으로 삭제됩니다.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    db.delete(portfolio)
    db.commit()
    return

@router.put(
    "/{portfolio_id}", 
    response_model=PortfolioResponse,
    summary="포트폴리오 수정",
    description="""
    ## 특정 포트폴리오의 정보를 수정합니다.
    
    ### 기능 설명
    - 포트폴리오의 모든 필드 수정 가능
    - 부분 업데이트 지원 (변경된 필드만 전송)
    - 대표 포트폴리오 설정 변경 가능
    
    ### 경로 파라미터
    - `portfolio_id`: 수정할 포트폴리오 ID
    
    ### 요청 데이터 (multipart/form-data)
    - `is_representative`: 대표 포트폴리오 여부 (선택사항)
    - `image`: 프로젝트 이미지 파일 (선택사항)
    - `project_url`: 프로젝트 URL (선택사항)
    - `project_name`: 프로젝트명 (선택사항)
    - `project_intro`: 프로젝트 소개 (선택사항)
    - `project_period`: 프로젝트 기간 (선택사항)
    - `role`: 프로젝트에서의 역할 (선택사항)
    
    ### 응답 데이터
    - 업데이트된 포트폴리오 정보
    
    ### 에러 응답
    - `404 Not Found`: 포트폴리오를 찾을 수 없음
    - `400 Bad Request`: 잘못된 요청 데이터
    """,
    responses={
        200: {
            "description": "포트폴리오 수정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "resume_id": 1,
                        "is_representative": True,
                        "image": "/media/profile/project1_updated.jpg",
                        "project_url": "https://github.com/user/project",
                        "project_name": "쇼핑몰 웹사이트 v2",
                        "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰 (업데이트됨)",
                        "project_period": "2024.01 - 2024.04",
                        "role": "풀스택 개발",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-02T00:00:00"
                    }
                }
            }
        },
        404: {
            "description": "포트폴리오를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "포트폴리오를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
def update_portfolio(
    portfolio_id: int = Path(..., description="수정할 포트폴리오 ID"),
    is_representative: Optional[bool] = Form(None, description="대표 포트폴리오 여부"),
    image: Optional[UploadFile] = File(None, description="프로젝트 이미지 파일"),
    project_url: Optional[str] = Form(None, description="프로젝트 URL"),
    project_name: Optional[str] = Form(None, description="프로젝트명"),
    project_intro: Optional[str] = Form(None, description="프로젝트 소개"),
    project_period: Optional[str] = Form(None, description="프로젝트 기간"),
    role: Optional[str] = Form(None, description="프로젝트에서의 역할"),
    db: Session = Depends(get_db),
):
    """
    특정 포트폴리오의 정보를 수정합니다.
    
    전송된 필드만 업데이트되며, 대표 포트폴리오 설정도 변경할 수 있습니다.
    """
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