-- LionConnect 커넥트 요청 테이블 마이그레이션 스크립트
-- DBeaver에서 실행하세요

-- 1. 기존 테이블이 있는지 확인
SELECT name FROM sqlite_master WHERE type='table' AND name='connect_request';

-- 2. 새로운 컬럼들 추가 (기존 테이블이 있는 경우)
ALTER TABLE connect_request ADD COLUMN company_representative_name VARCHAR(100) NOT NULL DEFAULT 'Unknown';
ALTER TABLE connect_request ADD COLUMN company_representative_email VARCHAR(100) NOT NULL DEFAULT 'unknown@example.com';
ALTER TABLE connect_request ADD COLUMN company_representative_phone VARCHAR(20) NOT NULL DEFAULT '000-0000-0000';
ALTER TABLE connect_request ADD COLUMN company_name VARCHAR(100);

-- 3. 테이블 구조 확인
PRAGMA table_info(connect_request);

-- 4. 샘플 데이터 확인 (있는 경우)
SELECT * FROM connect_request LIMIT 5;

-- 5. 인덱스 생성 (성능 향상을 위해)
CREATE INDEX IF NOT EXISTS idx_connect_request_student ON connect_request(student_user_id);
CREATE INDEX IF NOT EXISTS idx_connect_request_company_email ON connect_request(company_representative_email);
CREATE INDEX IF NOT EXISTS idx_connect_request_created_at ON connect_request(created_at);

-- 6. 테이블 정보 확인
SELECT 
    name,
    sql
FROM sqlite_master 
WHERE type='table' AND name='connect_request'; 