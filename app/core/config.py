import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.config import Config

# 환경 변수 설정
config = Config('.env')

# 개발 환경에서는 SQLite 사용 (파일이 없으면 메모리 DB)
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./test.db"  # 로컬 SQLite 파일 사용
)

# DB 종류에 따라 connect_args 분기
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OAuth 설정 (개발용 더미 값)
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='dummy_google_client_id')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='dummy_google_client_secret')
KAKAO_CLIENT_ID = config('KAKAO_CLIENT_ID', default='dummy_kakao_client_id')
KAKAO_CLIENT_SECRET = config('KAKAO_CLIENT_SECRET', default='dummy_kakao_client_secret')
OAUTH_REDIRECT_URL = config('OAUTH_REDIRECT_URL', default='http://localhost:8000/auth/callback')

# JWT 설정
SECRET_KEY = config('SECRET_KEY', default='lionconnect_secret_key_change_in_production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 