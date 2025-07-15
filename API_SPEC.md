# LionConnect API 명세서

---

## Resume (이력서)

### POST /resumes/basic-info/
- 이력서 기본 정보 생성 (프로필 이미지, 이름, 연락처, 학력 등)
- 요청: multipart/form-data
- 응답: 생성된 이력서 정보

### GET /resumes/{resume_id}/detail
- 특정 이력서의 상세 정보 전체 조회 (포트폴리오, 프로젝트, 수상, 교육 포함)
- 응답: 이력서 및 관련 데이터 전체

---

## Portfolio (포트폴리오)

### POST /portfolios/
- 포트폴리오 생성 (프로젝트 이미지, 대표 여부 등)
- 요청: multipart/form-data
- 응답: 생성된 포트폴리오 정보

### GET /portfolios?resume_id=1
- 특정 이력서의 포트폴리오 목록 조회
- 응답: 포트폴리오 배열

### PATCH /portfolios/{portfolio_id}/representative
- 특정 포트폴리오를 대표 포트폴리오로 설정
- 응답: 업데이트된 포트폴리오 정보

### PUT /portfolios/{portfolio_id}
- 포트폴리오 정보 수정 (부분 업데이트 지원)
- 요청: multipart/form-data
- 응답: 업데이트된 포트폴리오 정보

### DELETE /portfolios/{portfolio_id}
- 포트폴리오 삭제
- 응답: 204 No Content

---

## Project (프로젝트)

### POST /projects/
- 프로젝트 생성 (포트폴리오에 연결)
- 요청: multipart/form-data
- 응답: 생성된 프로젝트 정보

### GET /projects?portfolio_id=1
- 특정 포트폴리오의 프로젝트 목록 조회
- 응답: 프로젝트 배열

### PUT /projects/{project_id}
- 프로젝트 정보 수정 (부분 업데이트 지원)
- 요청: multipart/form-data
- 응답: 업데이트된 프로젝트 정보

### DELETE /projects/{project_id}
- 프로젝트 삭제
- 응답: 204 No Content

---

## Award (수상/자격증)

### POST /awards/
- 수상 및 활동 등록
- 요청: JSON
- 응답: 등록된 수상/활동 정보

---

## Education (교육)

### POST /educations/
- 교육 이력 등록
- 요청: JSON
- 응답: 등록된 교육 이력 정보

---

## Talent (인재)

### GET /talents/
- 인재 탐색 및 검색 (기술스택, 과정명 필터)
- 응답: 인재(포트폴리오) 배열

### POST /talents/connect-request
- 인재 연결 요청 (기업 → 학생)
- 요청: JSON
- 응답: 생성된 연결 요청 정보 