from sqlalchemy import create_engine, text
from app.core.config import SQLALCHEMY_DATABASE_URL
from app.models.user import Base, OAuthProviderEnum

def migrate_database():
    """
    소셜 로그인을 위한 데이터베이스 마이그레이션을 수행합니다.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # OAuthProviderEnum 타입이 존재하는지 확인
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'oauthproviderenum'
            );
        """))
        
        if not result.scalar():
            print("OAuthProviderEnum 타입을 생성합니다...")
            conn.execute(text("""
                CREATE TYPE oauthproviderenum AS ENUM ('google', 'kakao');
            """))
            conn.commit()
            print("OAuthProviderEnum 타입이 생성되었습니다.")
        else:
            print("OAuthProviderEnum 타입이 이미 존재합니다.")
        
        # user 테이블에 OAuth 관련 컬럼 추가
        try:
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS oauth_provider oauthproviderenum,
                ADD COLUMN IF NOT EXISTS oauth_id VARCHAR,
                ADD COLUMN IF NOT EXISTS name VARCHAR,
                ADD COLUMN IF NOT EXISTS profile_image VARCHAR;
            """))
            conn.commit()
            print("OAuth 관련 컬럼이 추가되었습니다.")
        except Exception as e:
            print(f"컬럼 추가 중 오류 발생: {e}")
        
        # password_hash 컬럼을 nullable로 변경
        try:
            conn.execute(text("""
                ALTER TABLE "user" 
                ALTER COLUMN password_hash DROP NOT NULL;
            """))
            conn.commit()
            print("password_hash 컬럼이 nullable로 변경되었습니다.")
        except Exception as e:
            print(f"password_hash 컬럼 변경 중 오류 발생: {e}")
        
        # 인덱스 생성
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_oauth 
                ON "user" (oauth_provider, oauth_id);
            """))
            conn.commit()
            print("OAuth 인덱스가 생성되었습니다.")
        except Exception as e:
            print(f"인덱스 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    print("소셜 로그인 데이터베이스 마이그레이션을 시작합니다...")
    migrate_database()
    print("마이그레이션이 완료되었습니다.") 