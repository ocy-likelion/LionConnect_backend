from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(
    title="🦁 LionConnect API (테스트)",
    description="""
    ## LionConnect - 학생과 기업을 연결하는 플랫폼 API (테스트 버전)
    
    ### 주요 기능
    - 🔐 **소셜 로그인**: Google, Kakao OAuth2 지원
    - 👨‍🎓 **학생 프로필**: 이력서, 포트폴리오 관리
    - 🏢 **기업 프로필**: 채용 정보, 기업 소개
    - 🤝 **매칭 시스템**: 학생과 기업 연결
    
    ### 개발 환경
    - **Base URL**: `http://localhost:8000`
    - **API 문서**: `/docs` (Swagger UI)
    - **대안 문서**: `/redoc` (ReDoc)
    """,
    version="2.0.0-test"
)

# 간단한 테스트 엔드포인트들
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LionConnect - 테스트</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { display: inline-block; padding: 10px 20px; margin: 10px; 
                   background: #007bff; color: white; text-decoration: none; 
                   border-radius: 5px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦁 LionConnect API 테스트</h1>
            <p>API 문서를 확인하려면 아래 링크를 클릭하세요:</p>
            <a href="/docs" class="btn">Swagger UI 문서</a>
            <a href="/redoc" class="btn">ReDoc 문서</a>
            <hr>
            <h2>테스트 엔드포인트</h2>
            <ul>
                <li><a href="/test">GET /test</a> - 기본 테스트</li>
                <li><a href="/health">GET /health</a> - 서버 상태 확인</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.get("/test")
def test_endpoint():
    return {"message": "LionConnect API가 정상적으로 작동합니다!", "status": "success"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}

@app.get("/auth/test", summary="인증 테스트", description="인증 시스템이 정상 작동하는지 테스트합니다.")
def auth_test():
    return {
        "message": "인증 시스템 테스트",
        "oauth_providers": ["google", "kakao"],
        "status": "ready"
    }

@app.get("/resumes/test", summary="이력서 테스트", description="이력서 API가 정상 작동하는지 테스트합니다.")
def resume_test():
    return {
        "message": "이력서 시스템 테스트",
        "features": ["기본 정보 생성", "상세 정보 조회"],
        "status": "ready"
    }

@app.get("/portfolios/test", summary="포트폴리오 테스트", description="포트폴리오 API가 정상 작동하는지 테스트합니다.")
def portfolio_test():
    return {
        "message": "포트폴리오 시스템 테스트",
        "features": ["포트폴리오 생성", "목록 조회", "대표 설정"],
        "status": "ready"
    }

@app.get("/projects/test", summary="프로젝트 테스트", description="프로젝트 API가 정상 작동하는지 테스트합니다.")
def project_test():
    return {
        "message": "프로젝트 시스템 테스트",
        "features": ["프로젝트 생성", "목록 조회", "수정/삭제"],
        "status": "ready"
    }

@app.get("/talents/test", summary="인재 매칭 테스트", description="인재 매칭 API가 정상 작동하는지 테스트합니다.")
def talent_test():
    return {
        "message": "인재 매칭 시스템 테스트",
        "features": ["인재 검색", "연결 요청"],
        "status": "ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 