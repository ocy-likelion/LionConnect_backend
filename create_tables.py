from sqlalchemy import create_engine, text
from app.core.config import SQLALCHEMY_DATABASE_URL
from app.models.user import Base, User, StudentProfile, CompanyProfile, OAuthProviderEnum, UserTypeEnum
from app.models.resume import ResumeBasicInfo
from app.models.portfolio import Portfolio
from app.models.project import Project
from app.models.award import Award
from app.models.education import Education
from app.models.connect import ConnectRequest
from datetime import datetime

def create_tables():
    """
    SQLite 데이터베이스에 테이블을 생성합니다.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
    
    # 테스트 데이터 생성 (선택사항)
    with engine.connect() as conn:
        # 테스트 사용자 생성
        test_user = User(
            id=1,
            email="test@example.com",
            user_type=UserTypeEnum.student,
            oauth_provider=OAuthProviderEnum.google,
            oauth_id="12345",
            name="테스트 사용자",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 테스트 이력서 생성
        test_resume = ResumeBasicInfo(
            id=1,
            user_id=1,
            name="홍길동",
            email="hong@example.com",
            phone="010-1234-5678",
            job_type="프론트엔드 개발자",
            school="서울대학교",
            major="컴퓨터공학과",
            grade="4학년",
            period="2020-2024",
            short_intro="웹 개발에 열정을 가진 학생입니다.",
            intro="프론트엔드 개발에 관심이 많아 React, Vue.js 등을 학습하고 있습니다.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 테스트 포트폴리오 생성
        test_portfolio = Portfolio(
            id=1,
            resume_id=1,
            is_representative=True,
            project_name="쇼핑몰 웹사이트",
            project_intro="React와 Node.js를 활용한 풀스택 쇼핑몰",
            project_period="2024.01 - 2024.03",
            role="프론트엔드 개발",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 테스트 프로젝트 생성
        test_project = Project(
            id=1,
            portfolio_id=1,
            project_name="쇼핑몰 결제 시스템",
            project_period="2024.01 - 2024.02",
            project_intro="온라인 쇼핑몰의 결제 시스템 개발",
            description="사용자가 상품을 선택하고 결제할 수 있는 시스템을 개발했습니다.",
            role="백엔드 개발",
            tech_stack="Node.js, Express, MongoDB, JWT",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 데이터베이스에 저장
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            db.add(test_user)
            db.add(test_resume)
            db.add(test_portfolio)
            db.add(test_project)
            db.commit()
            print("✅ 테스트 데이터가 성공적으로 생성되었습니다!")
        except Exception as e:
            print(f"⚠️ 테스트 데이터 생성 중 오류: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    print("🗄️ 데이터베이스 테이블 생성을 시작합니다...")
    create_tables()
    print("🎉 완료!") 