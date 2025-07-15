from sqlalchemy import create_engine
from app.core.config import SQLALCHEMY_DATABASE_URL
from app.models.user import Base

def create_tables():
    """
    데이터베이스에 테이블을 생성합니다.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    print("🗄️ 데이터베이스 테이블 생성을 시작합니다...")
    create_tables()
    print("🎉 완료!") 