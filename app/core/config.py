import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 기본 설정
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', None)

# 데이터베이스 설정
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
