import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 환경 변수 직접 로딩 (Config 객체 사용하지 않음 - 타임아웃 방지)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'dummy_google_client_id')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'dummy_google_client_secret')
KAKAO_CLIENT_ID = os.environ.get('KAKAO_CLIENT_ID', 'dummy_kakao_client_id')
KAKAO_CLIENT_SECRET = os.environ.get('KAKAO_CLIENT_SECRET', 'dummy_kakao_client_secret')

# OAuth 리다이렉트 URI 설정
# 백엔드 콜백 URI (카카오 개발자 콘솔에 등록할 URI)
KAKAO_BACKEND_CALLBACK_URI = os.environ.get(
    'KAKAO_BACKEND_CALLBACK_URI', 
    'https://lionconnect-backend.onrender.com/auth/callback/kakao'
)

# 프론트엔드 리다이렉트 URI (실제 사용자 리다이렉트)
FRONTEND_REDIRECT_URI = os.environ.get(
    'FRONTEND_REDIRECT_URI',
    'https://lion-connect.vercel.app/auth/kakao/callback'
)

# 개발 환경용 프론트엔드 URI
FRONTEND_DEV_REDIRECT_URI = os.environ.get(
    'FRONTEND_DEV_REDIRECT_URI',
    'http://localhost:3000/auth/kakao/callback'
)

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', None)

# 개발 환경에서 SQLite 사용 (파일 기반 또는 메모리 DB)
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://lionconnect_user:gKIoR3YWUjnOjpbZgPXWygVncYMaSi0o@dpg-d1mek9e3jp1c73ennt6g-a/lionconnect"
)

# DB 종류에 따라 connect_args 분기
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL 연결 최적화 (타임아웃 방지)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # 연결 상태 확인
        pool_recycle=300,    # 5분마다 연결 재생성
        pool_size=5,         # 연결 풀 크기 줄임
        max_overflow=10,     # 최대 오버플로우 줄임
        echo=False,          # SQL 로그 비활성화 (배포 시 성능 향상)
        connect_args={
            "connect_timeout": 10,  # 연결 타임아웃 설정
            "application_name": "lionconnect"
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
