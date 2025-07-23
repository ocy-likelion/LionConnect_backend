from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import resume, portfolio, project, auth, talent
import os
from app.routers.award import router as award_router
from app.routers.education import router as education_router
from app.routers.connect import router as connect_router

app = FastAPI(
    title="🦁 LionConnect API",
    description="""
    ## LionConnect - 학생과 기업을 연결하는 플랫폼 API
    
    ### 주요 기능
    - 🔐 **소셜 로그인**: Google, Kakao OAuth2 지원
    - 👨‍🎓 **학생 프로필**: 이력서, 포트폴리오 관리
    - 🏢 **기업 프로필**: 채용 정보, 기업 소개
    - 🤝 **매칭 시스템**: 학생과 기업 연결
    - 🔗 **커넥트 요청**: 기업담당자의 수료생 연결 요청
    
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
        },
        {
            "name": "Connect",
            "description": "커넥트 요청 API - 기업담당자의 수료생 연결 요청"
        }
    ]
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:3001",  # 다른 포트의 개발 서버
        "https://lion-connect.vercel.app",  # 프로덕션 프론트엔드 도메인 (실제 도메인으로 변경 필요)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 정적 파일 제공 (업로드된 이미지 등)
app.mount("/media", StaticFiles(directory="app/media"), name="media")

# 라우터 등록
app.include_router(resume.router)
app.include_router(portfolio.router)
app.include_router(project.router)
app.include_router(auth.router)
app.include_router(talent.router)
app.include_router(award_router)
app.include_router(education_router)
app.include_router(connect_router)

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

@app.get("/connect-request", response_class=HTMLResponse)
def connect_request_form(request: Request):
    return templates.TemplateResponse("connect_request.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

import os
os.makedirs("app/media/profile", exist_ok=True) 