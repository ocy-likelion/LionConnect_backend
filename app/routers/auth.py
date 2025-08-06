from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.core.config import get_db
from app.models.user import User, UserTypeEnum
from app.schemas.user import UserCreateStudent, UserCreateCompany, UserResponse, LoginRequest, TokenResponse
from app.utils.auth import create_access_token, verify_token
import logging
from datetime import timedelta

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ====== 기본 로그인/회원가입 ======
@router.post("/signup/student", response_model=UserResponse, 
    summary="학생 회원가입",
    description="""
    학생 사용자 회원가입 API
    
    ### 요청 데이터
    - `email`: 이메일 주소 (유니크)
    - `password`: 비밀번호 (최소 8자)
    - `name`: 사용자 이름
    
    ### 응답 데이터
    - `id`: 사용자 ID
    - `email`: 이메일 주소
    - `name`: 사용자 이름
    - `user_type`: 사용자 타입 (student)
    - `created_at`: 생성 시간
    
    ### 에러 코드
    - `400`: 이미 존재하는 이메일
    - `422`: 유효하지 않은 데이터 형식
    """)
def signup_student(user: UserCreateStudent, db: Session = Depends(get_db)):
    """
    학생 회원가입
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    # 새 사용자 생성
    new_user = User(
        email=user.email,
        name=user.name,
        user_type=UserTypeEnum.student
    )
    new_user.set_password(user.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/signup/company", response_model=UserResponse,
    summary="기업 회원가입",
    description="""
    기업 사용자 회원가입 API
    
    ### 요청 데이터
    - `email`: 이메일 주소 (유니크)
    - `password`: 비밀번호 (최소 8자)
    - `name`: 담당자 이름
    - `company_name`: 회사명
    
    ### 응답 데이터
    - `id`: 사용자 ID
    - `email`: 이메일 주소
    - `name`: 담당자 이름
    - `company_name`: 회사명
    - `user_type`: 사용자 타입 (company)
    - `created_at`: 생성 시간
    
    ### 에러 코드
    - `400`: 이미 존재하는 이메일
    - `422`: 유효하지 않은 데이터 형식
    """)
def signup_company(user: UserCreateCompany, db: Session = Depends(get_db)):
    """
    기업 회원가입
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    # 새 사용자 생성
    new_user = User(
        email=user.email,
        name=user.name,
        company_name=user.company_name,
        user_type=UserTypeEnum.company
    )
    new_user.set_password(user.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=TokenResponse,
    summary="로그인",
    description="""
    사용자 로그인 API
    
    ### 요청 데이터
    - `email`: 이메일 주소
    - `password`: 비밀번호
    
    ### 응답 데이터
    - `access_token`: JWT 액세스 토큰
    - `user`: 사용자 정보 객체
        - `id`: 사용자 ID
        - `email`: 이메일 주소
        - `name`: 사용자 이름
        - `user_type`: 사용자 타입
        - `company_name`: 회사명 (기업 사용자만)
    
    ### 토큰 사용법
    이후 API 요청 시 Authorization 헤더에 포함:
    ```
    Authorization: Bearer {access_token}
    ```
    
    ### 에러 코드
    - `401`: 이메일 또는 비밀번호가 잘못됨
    - `422`: 유효하지 않은 데이터 형식
    """)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    기본 로그인 (이메일/비밀번호)
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not user.check_password(request.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    return TokenResponse(access_token=access_token, user=user)

@router.get("/me", response_model=UserResponse,
    summary="현재 사용자 정보 조회",
    description="""
    현재 로그인한 사용자의 정보를 조회하는 API
    
    ### 인증 필요
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    
    ### 응답 데이터
    - `id`: 사용자 ID
    - `email`: 이메일 주소
    - `name`: 사용자 이름
    - `user_type`: 사용자 타입
    - `company_name`: 회사명 (기업 사용자만)
    - `created_at`: 생성 시간
    - `updated_at`: 수정 시간
    
    ### 에러 코드
    - `401`: 인증 토큰이 없거나 유효하지 않음
    - `404`: 사용자를 찾을 수 없음
    """)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자 정보 조회
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="토큰에 사용자 정보가 없습니다.")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

@router.post("/logout",
    summary="로그아웃",
    description="""
    사용자 로그아웃 API
    
    ### 참고사항
    - 서버에서는 토큰을 무효화하지 않습니다
    - 클라이언트에서 토큰을 삭제하여 로그아웃 처리
    - 보안을 위해 클라이언트에서 토큰을 완전히 제거하세요
    
    ### 응답 데이터
    - `message`: 로그아웃 완료 메시지
    """)
async def logout():
    """
    로그아웃 (클라이언트에서 토큰 삭제)
    """
    return {"message": "로그아웃되었습니다."}
