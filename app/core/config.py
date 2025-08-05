import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.config import Config

# ?�경 변???�정
config = Config('.env')

# 개발 ?�경?�서??SQLite ?�용 (?�일???�으�?메모�?DB)
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://lionconnect_user:gKIoR3YWUjnOjpbZgPXWygVncYMaSi0o@dpg-d1mek9e3jp1c73ennt6g-a/lionconnect"
)

# DB 종류???�라 connect_args 분기
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL ?�결 최적??
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # ?�결 ?�태 ?�인
        pool_recycle=300,    # 5분마???�결 ?�생??
        pool_size=10,        # ?�결 ?� ?�기
        max_overflow=20,     # 최�? ?�버?�로??
        echo=False           # SQL 로그 비활?�화 (배포 ???�능 ?�상)
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB ?�존???�수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth ?�정 (개발???��? �?
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='dummy_google_client_id')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='dummy_google_client_secret')
KAKAO_CLIENT_ID = config('KAKAO_CLIENT_ID', default='dummy_kakao_client_id')
KAKAO_CLIENT_SECRET = config('KAKAO_CLIENT_SECRET', default='dummy_kakao_client_secret')
KAKAO_REDIRECT_URI = config('KAKAO_REDIRECT_URI', default='https://lionconnect-backend.onrender.com/auth/callback/kakao')
# JWT ?�정
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Slack ?�훅 URL
SLACK_WEBHOOK_URL = config('SLACK_WEBHOOK_URL', default=None)
