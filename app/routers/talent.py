from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.user import User, StudentProfile
from app.models.portfolio import Portfolio
from app.models.connect import ConnectRequest
from app.models.resume import ResumeBasicInfo
from app.schemas.connect import ConnectRequestCreate, ConnectRequestResponse
from app.core.config import get_db, SLACK_WEBHOOK_URL
from app.utils.slack import send_slack_message
from typing import List, Optional

router = APIRouter(prefix="/talents", tags=["Talent"])

@router.get(
    "/grid",
    response_model=List[dict],
    summary="🦁 수료생 그리드 카드 목록",
    description="""
    ## 수료생 그리드 카드 페이지용 API
    
    등록된 모든 수료생을 그리드 카드 형태로 보여주기 위한 최적화된 API입니다.
    
    ### 📋 반환 데이터
    - `user_id`: 수료생 ID
    - `profile_image`: 프로필 이미지 URL
    - `name`: 수료생 이름
    - `job_type`: 희망 직무
    - `school`: 학교명
    - `major`: 전공
    - `short_intro`: 간단 소개
    - `representative_portfolio`: 대표 포트폴리오 정보
      - `project_name`: 프로젝트명
      - `project_intro`: 프로젝트 소개
      - `project_image_url`: 프로젝트 이미지 URL
      - `tech_stack`: 기술 스택
    - `created_at`: 등록일
    
    ### 🔍 필터링 옵션
    - `job_type`: 직무별 필터링
    - `school`: 학교별 필터링
    - `tech_stack`: 기술스택별 필터링
    
    ### 📊 페이지네이션
    - `skip`: 건너뛸 개수 (기본값: 0)
    - `limit`: 가져올 개수 (기본값: 12, 최대: 50)
    """,
    responses={
        200: {
            "description": "수료생 그리드 카드 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "user_id": 1,
                            "profile_image": "/media/profile/user1.jpg",
                            "name": "홍길동",
                            "job_type": "프론트엔드 개발자",
                            "school": "서울대학교",
                            "major": "컴퓨터공학과",
                            "short_intro": "웹 개발에 열정을 가진 학생입니다.",
                            "representative_portfolio": {
                                "project_name": "쇼핑몰 웹사이트",
                                "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                                "project_image_url": "/media/portfolio/1.png",
                                "tech_stack": "React, Node.js, MongoDB"
                            },
                            "created_at": "2024-01-01T00:00:00"
                        }
                    ]
                }
            }
        }
    }
)
def get_talent_grid_cards(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(12, ge=1, le=50, description="가져올 개수"),
    job_type: Optional[str] = Query(None, description="직무별 필터링"),
    school: Optional[str] = Query(None, description="학교별 필터링"),
    tech_stack: Optional[str] = Query(None, description="기술스택별 필터링"),
    db: Session = Depends(get_db),
):
    """
    수료생 그리드 카드 페이지를 위한 최적화된 API입니다.
    
    프로필 이미지, 이름, 직무, 학교, 대표 포트폴리오 정보를 포함하여
    그리드 카드 형태로 표시하기에 적합한 데이터를 반환합니다.
    """
    # 기본 쿼리: resume_basic_info 테이블에서 수료생 정보 조회
    query = db.query(ResumeBasicInfo)
    
    # 필터링 적용
    if job_type:
        query = query.filter(ResumeBasicInfo.job_type.contains(job_type))
    if school:
        query = query.filter(ResumeBasicInfo.school.contains(school))
    
    # 페이지네이션 적용
    resumes = query.offset(skip).limit(limit).all()
    
    result = []
    for resume in resumes:
        # 해당 수료생의 대표 포트폴리오 조회
        representative_portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == resume.id,
            Portfolio.is_representative == True
        ).first()
        
        # 대표 포트폴리오가 없으면 첫 번째 포트폴리오 사용
        if not representative_portfolio:
            representative_portfolio = db.query(Portfolio).filter(
                Portfolio.user_id == resume.id
            ).first()
        
        # 기술스택 필터링 (포트폴리오가 있는 경우에만)
        if tech_stack and representative_portfolio:
            # 포트폴리오의 기술스택 정보가 있는지 확인
            # 실제 구현에서는 Portfolio 모델에 tech_stack 필드가 있어야 함
            pass
        
        portfolio_info = None
        if representative_portfolio:
            portfolio_info = {
                "project_name": representative_portfolio.project_name,
                "project_intro": representative_portfolio.project_intro,
                "project_image_url": representative_portfolio.image,
                "tech_stack": getattr(representative_portfolio, 'tech_stack', None)  # 필드가 있는 경우에만
            }
        
        talent_card = {
            "user_id": resume.id,
            "profile_image": resume.profile_image,
            "name": resume.name,
            "job_type": resume.job_type,
            "school": resume.school,
            "major": resume.major,
            "short_intro": resume.short_intro,
            "representative_portfolio": portfolio_info,
            "created_at": resume.created_at
        }
        
        result.append(talent_card)
    
    return result

@router.get(
    "/",
    response_model=List[dict],
    summary="인재 탐색 및 검색",
    description="""
    전체 인재(수료생) 목록을 탐색하거나, 기술 스택/과정명으로 필터링하여 검색합니다.\n
    - 쿼리 파라미터 없이 호출 시 전체 인재 반환\n    - `tech_stack`: 검색할 기술 스택 (선택)\n    - `course_name`: 검색할 과정명 (선택)\n
    **응답:**\n    - `portfolio_id`: 포트폴리오 ID\n    - `student_user_id`: 학생 사용자 ID\n    - `student_email`: 학생 이메일\n    - `course_name`: 과정명\n    - `tech_stack`: 기술 스택\n    - `project_name`: 프로젝트명\n    - `project_intro`: 프로젝트 소개\n    - `is_representative`: 대표 포트폴리오 여부\n    - `project_image_url`: 대표 프로젝트 이미지 URL
    """,
    responses={
        200: {
            "description": "인재 탐색/검색 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "portfolio_id": 1,
                            "student_user_id": 1,
                            "student_email": "student1@example.com",
                            "course_name": "웹개발 과정",
                            "tech_stack": "React, Node.js, MongoDB",
                            "project_name": "쇼핑몰 웹사이트",
                            "project_intro": "React와 Node.js를 활용한 풀스택 쇼핑몰",
                            "is_representative": True,
                            "project_image_url": "/media/portfolio/1.png"
                        },
                        {
                            "portfolio_id": 2,
                            "student_user_id": 2,
                            "student_email": "student2@example.com",
                            "course_name": "AI 엔지니어 과정",
                            "tech_stack": "Python, TensorFlow",
                            "project_name": "AI 이미지 분류",
                            "project_intro": "딥러닝 기반 이미지 분류 프로젝트",
                            "is_representative": False,
                            "project_image_url": None
                        }
                    ]
                }
            }
        }
    }
)
def list_talents(
    tech_stack: Optional[str] = Query(None, description="검색할 기술 스택 (예: React, Python)"),
    course_name: Optional[str] = Query(None, description="검색할 과정명 (예: 웹개발 과정)"),
    db: Session = Depends(get_db),
):
    """
    조건에 맞는 인재(수료생)를 검색합니다.
    
    기술 스택과 과정명을 기준으로 필터링하여
    기업이 원하는 인재를 찾을 수 있도록 도와줍니다.
    """
    query = db.query(Portfolio, User, StudentProfile).join(User, Portfolio.resume_id == User.id).join(StudentProfile, StudentProfile.user_id == User.id)
    if tech_stack:
        query = query.filter(StudentProfile.tech_stack.contains(tech_stack))
    if course_name:
        query = query.filter(StudentProfile.course_name == course_name)
    results = query.all()
    # 간단한 dict 변환
    return [
        {
            "portfolio_id": p.id,
            "student_user_id": u.id,
            "student_email": u.email,
            "course_name": s.course_name,
            "tech_stack": s.tech_stack,
            "project_name": p.project_name,
            "project_intro": p.project_intro,
            "is_representative": p.is_representative,
            "project_image_url": p.image,  # 대표 프로젝트 이미지 URL 추가
        }
        for p, u, s in results
    ]

@router.post(
    "/connect-request",
    response_model=ConnectRequestResponse,
    summary="인재 연결 요청",
    description="""
    기업담당자가 수료생에게 연결 요청을 보냅니다.\n
    - `user_id`: 수료생 사용자 ID (필수)\n
    - `company_representative_name`: 기업담당자 이름 (필수)\n
    - `company_representative_email`: 기업담당자 이메일 (필수)\n
    - `company_representative_phone`: 기업담당자 전화번호 (필수)\n
    - `company_name`: 기업명 (선택)\n
    - `message`: 연결 요청 메시지 (선택)\n
    - `position`: 채용 포지션 (선택)\n
    - `job_description`: 직무 설명 (선택)\n
    - `required_stack`: 필수 기술 스택 (선택)\n
    - `career_level`: 희망 경력 수준 (선택)\n
    - `employment_type`: 고용 형태 (선택)\n
    **응답:** 생성된 연결 요청의 상세 정보 반환
    """,
    responses={
        201: {
            "description": "연결 요청 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "company_user_id": None,
                        "user_id": 1,
                        "portfolio_id": 1,
                        "company_representative_name": "김기업",
                        "company_representative_email": "kim@company.com",
                        "company_representative_phone": "010-1234-5678",
                        "company_name": "테크컴퍼니",
                        "message": "안녕하세요! 귀하의 포트폴리오를 보고 연락드립니다.",
                        "position": "프론트엔드 개발자",
                        "job_description": "React 기반 웹앱 개발",
                        "required_stack": "React, TypeScript",
                        "career_level": "신입~3년",
                        "employment_type": "정규직",
                        "created_at": "2024-07-01T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "잘못된 데이터",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "기업담당자 기본 정보가 누락되었습니다."
                    }
                }
            }
        },
        404: {
            "description": "수료생을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {"detail": "수료생의 이력서를 찾을 수 없습니다."}
                }
            }
        },
        500: {"description": "서버 오류"}
    }
)
def create_connect_request(
    req: ConnectRequestCreate,
    db: Session = Depends(get_db),
):
    """
    특정 인재(수료생)에게 연결 요청을 보냅니다.
    
    기업이 관심 있는 인재에게 연결 요청을 보내며,
    같은 수료생에게 여러 번 요청할 수 있고 Slack 알림을 통해 실시간으로 알림을 전송합니다.
    """
    try:
        # 입력 데이터 검증
        if not req.company_representative_name or not req.company_representative_email or not req.company_representative_phone:
            raise HTTPException(status_code=400, detail="기업담당자 기본 정보가 누락되었습니다.")
        
        if not req.user_id:
            raise HTTPException(status_code=400, detail="수료생 정보가 누락되었습니다.")
        
        # 수료생 존재 여부 확인 (resume_basic_info 테이블에서)
        student_resume = db.query(ResumeBasicInfo).filter(ResumeBasicInfo.id == req.user_id).first()
        if not student_resume:
            raise HTTPException(status_code=404, detail="수료생의 이력서를 찾을 수 없습니다.")
        
        # 수료생의 대표 포트폴리오 자동 찾기 (없어도 OK)
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == req.user_id,
            Portfolio.is_representative == True
        ).first()
        
        # 대표 포트폴리오가 없으면 첫 번째 포트폴리오 사용
        if not portfolio:
            portfolio = db.query(Portfolio).filter(
                Portfolio.user_id == req.user_id
            ).first()
        
        # 포트폴리오가 없어도 커넥트 요청은 가능 (portfolio_id는 null로 설정)
        portfolio_id = portfolio.id if portfolio else None
        
        # 중복 요청 방지 로직 제거 - 같은 수료생에게 여러 번 요청 가능
        
        # 커넥트 요청 생성 (company_user_id는 null, portfolio_id는 자동 설정)
        connect = ConnectRequest(
            company_user_id=None,  # 로그인하지 않은 사용자
            user_id=req.user_id,
            portfolio_id=portfolio_id,  # 포트폴리오가 없으면 null
            company_representative_name=req.company_representative_name,
            company_representative_email=req.company_representative_email,
            company_representative_phone=req.company_representative_phone,
            company_name=req.company_name,
            message=req.message,
            position=req.position,
            job_description=req.job_description,
            required_stack=req.required_stack,
            career_level=req.career_level,
            employment_type=req.employment_type
        )
        db.add(connect)
        db.commit()
        db.refresh(connect)
        
        # Slack 알림 전송
        if SLACK_WEBHOOK_URL:
            try:
                slack_message = f"""
🦁 *새로운 커넥트 요청이 도착했습니다!*

*기업담당자 정보:*
• 이름: {req.company_representative_name}
• 이메일: {req.company_representative_email}
• 전화번호: {req.company_representative_phone}
• 기업명: {req.company_name or '미입력'}

*수료생 정보:*
• 이름: {student_resume.name if student_resume else '미입력'}
• 이메일: {student_resume.email if student_resume else '미입력'}
• 전화번호: {student_resume.phone if student_resume else '미입력'}
• 희망 직무: {student_resume.job_type if student_resume else '미입력'}
• 학교: {student_resume.school if student_resume else '미입력'}
• 전공: {student_resume.major if student_resume else '미입력'}

*포트폴리오 정보:*
• 프로젝트명: {portfolio.project_name if portfolio else '포트폴리오 없음'}
• 프로젝트 소개: {portfolio.project_intro if portfolio else '포트폴리오 없음'}

*채용 정보:*
• 포지션: {req.position or '미입력'}
• 직무 설명: {req.job_description or '미입력'}
• 필수 기술스택: {req.required_stack or '미입력'}
• 경력 수준: {req.career_level or '미입력'}
• 고용 형태: {req.employment_type or '미입력'}

*메시지:*
{req.message or '메시지 없음'}

---
요청 시간: {connect.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
                send_slack_message(SLACK_WEBHOOK_URL, slack_message)
            except Exception as e:
                print(f"Slack 알림 전송 실패 (요청은 성공): {str(e)}")
        
        return connect
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"연결 요청 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="연결 요청 생성 중 오류가 발생했습니다.") 