from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routers import resume, portfolio, project, auth, talent
import os
from app.routers.award import router as award_router
from app.routers.education import router as education_router

app = FastAPI(
    title="🦁 LionConnect API",
    description="""
    ## LionConnect - 학생과 기업을 연결하는 플랫폼 API
    
    ### 주요 기능
    - 🔐 **소셜 로그인**: Google, Kakao OAuth2 지원
    - 👨‍🎓 **학생 프로필**: 이력서, 포트폴리오 관리
    - 🏢 **기업 프로필**: 채용 정보, 기업 소개
    - 🤝 **매칭 시스템**: 학생과 기업 연결
    
    ### 인증 방식
    - JWT Bearer Token 사용
    - 소셜 로그인 후 자동 토큰 발급
    - 토큰은 Authorization 헤더에 `Bearer {token}` 형태로 전송
    
    ### 사용자 유형
    - **student**: 수료생 (이력서, 포트폴리오 작성)
    - **company**: 기업 (채용 정보, 학생 검색)
    
    ### 개발 환경
    - **Base URL**: `http://localhost:8000`
    - **API 문서**: `/docs` (Swagger UI)
    - **대안 문서**: `/redoc` (ReDoc)
    
    ### 소셜 로그인 플로우
    1. 사용자가 소셜 로그인 버튼 클릭
    2. OAuth 제공자(Google/Kakao)로 리디렉트
    3. 인증 완료 후 백엔드 콜백 URL로 리디렉트
    4. 백엔드에서 사용자 정보 처리 및 JWT 토큰 생성
    5. 클라이언트로 토큰 반환
    """,
    version="2.0.0",
    contact={
        "name": "LionConnect Team",
        "email": "support@lionconnect.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Auth",
            "description": "인증 관련 API - 소셜 로그인, 토큰 관리"
        },
        {
            "name": "Resume",
            "description": "이력서 관리 API - 학생 이력서 작성 및 관리"
        },
        {
            "name": "Portfolio",
            "description": "포트폴리오 관리 API - 프로젝트 포트폴리오 작성 및 관리"
        },
        {
            "name": "Project",
            "description": "프로젝트 관리 API - 개별 프로젝트 정보 관리"
        },
        {
            "name": "Talent",
            "description": "인재 매칭 API - 기업의 인재 검색 및 연결"
        }
    ]
)

# OAuth 미들웨어는 사용하지 않음 (app.add_middleware(oauth) 삭제)

app.include_router(resume.router)
app.include_router(portfolio.router)
app.include_router(project.router)
app.include_router(auth.router)
app.include_router(talent.router)
app.include_router(award_router)
app.include_router(education_router)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/resume-form", response_class=HTMLResponse)
def resume_form(request: Request):
    return templates.TemplateResponse("resume_form.html", {"request": request})

@app.get("/portfolio-form", response_class=HTMLResponse)
def portfolio_form(request: Request):
    return templates.TemplateResponse("portfolio_form.html", {"request": request})

@app.get("/project-form", response_class=HTMLResponse)
def project_form(request: Request):
    return templates.TemplateResponse("project_form.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request}) 