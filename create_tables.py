from sqlalchemy import create_engine
from app.core.config import SQLALCHEMY_DATABASE_URL

# 모든 모델 import
from app.models.user import Base as UserBase
from app.models.resume import Base as ResumeBase
from app.models.portfolio import Base as PortfolioBase
from app.models.project import Base as ProjectBase
from app.models.education import Base as EducationBase
from app.models.award import Base as AwardBase
from app.models.connect import Base as ConnectBase

def create_tables():
    """
    데이터베이스에 테이블을 생성합니다.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # 모든 테이블 생성
    UserBase.metadata.create_all(bind=engine)
    ResumeBase.metadata.create_all(bind=engine)
    PortfolioBase.metadata.create_all(bind=engine)
    ProjectBase.metadata.create_all(bind=engine)
    EducationBase.metadata.create_all(bind=engine)
    AwardBase.metadata.create_all(bind=engine)
    ConnectBase.metadata.create_all(bind=engine)
    
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    print("🗄️ 데이터베이스 테이블 생성을 시작합니다...")
    create_tables()
    print("🎉 완료!") 