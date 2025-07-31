import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.config import Config

# 환경 변수 설정
config = Config('.env')

# 개발 환경에서는 SQLite 사용 (파일이 없으면 메모리 DB)
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
    # PostgreSQL 연결 최적화
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # 연결 상태 확인
        pool_recycle=300,    # 5분마다 연결 재생성
        pool_size=10,        # 연결 풀 크기
        max_overflow=20,     # 최대 오버플로우
        echo=False           # SQL 로그 비활성화 (배포 시 성능 향상)
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth 설정 (개발용 더미 값)
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='dummy_google_client_id')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='dummy_google_client_secret')
KAKAO_CLIENT_ID = config('KAKAO_CLIENT_ID', default='dummy_kakao_client_id')
KAKAO_CLIENT_SECRET = config('KAKAO_CLIENT_SECRET', default='dummy_kakao_client_secret')

# JWT 설정
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Slack 웹훅 URL
SLACK_WEBHOOK_URL = config('SLACK_WEBHOOK_URL', default=None)