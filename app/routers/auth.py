from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, TokenResponse, OAuthLoginRequest, OAuthCallbackResponse, LoginRequest, UserCreateStudent, UserCreateCompany, UserTypeEnum
from app.models.user import User, StudentProfile, CompanyProfile, OAuthProviderEnum
from app.core.config import SessionLocal
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.oauth import oauth, get_or_create_user, get_kakao_user_info_async
from datetime import timedelta
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ====== 기존 회원가입/로그인 API ======
@router.post("/signup/student", response_model=UserResponse)
def signup_student(user: UserCreateStudent, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user_obj = User(
        email=user.email,
        password_hash=hash_password(user.password),
        user_type=UserTypeEnum.student,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    profile = StudentProfile(
        user_id=user_obj.id,
        course_name=user.course_name,
        course_generation=user.course_generation,
        tech_stack=user.tech_stack,
    )
    db.add(profile)
    db.commit()
    return user_obj

@router.post("/signup/company", response_model=UserResponse)
def signup_company(user: UserCreateCompany, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    user_obj = User(
        email=user.email,
        password_hash=hash_password(user.password),
        user_type=UserTypeEnum.company,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    profile = CompanyProfile(
        user_id=user_obj.id,
        company_name=user.company_name,
        industry=user.industry,
        size=user.size,
        intro=user.intro,
        email_verified=False,
    )
    db.add(profile)
    db.commit()
    return user_obj

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    return TokenResponse(access_token=access_token, user=user)

# ====== 카카오 OAuth 로그인 엔드포인트 ======
@router.get("/login/kakao")
async def kakao_login(
    request: Request,
    user_type: UserTypeEnum = Query(UserTypeEnum.student, description="사용자 유형")
):
    """
    카카오 OAuth 로그인을 시작합니다.
    """
    # 카카오 OAuth가 설정되지 않은 경우
    if not hasattr(oauth, 'kakao'):
        raise HTTPException(
            status_code=503, 
            detail="카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요."
        )
    
    redirect_uri = "https://lionconnect-backend.onrender.com/auth/callback/kakao"
    return await oauth.kakao.authorize_redirect(
        request=request,
        redirect_uri=redirect_uri,
        scope="profile_nickname profile_image account_email",
        state=user_type.value
    )

@router.get("/callback/kakao", response_model=OAuthCallbackResponse)
async def kakao_callback(
    request: Request,
    code: str = Query(..., description="카카오에서 받은 인증 코드"),
    state: str = Query(..., description="사용자 유형"),
    db: Session = Depends(get_db)
):
    """
    카카오 OAuth 콜백을 처리합니다.
    """
    # 카카오 OAuth가 설정되지 않은 경우
    if not hasattr(oauth, 'kakao'):
        raise HTTPException(
            status_code=503, 
            detail="카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요."
        )
    
    try:
        # 사용자 유형 파싱
        user_type = UserTypeEnum(state)
    except ValueError:
        user_type = UserTypeEnum.student
    
    # 액세스 토큰 획득
    token = await oauth.kakao.authorize_access_token(request)
    
    # 사용자 정보 가져오기
    user_info = await get_kakao_user_info_async(request, token)
    
    # 사용자 찾기 또는 생성
    user = get_or_create_user(db, OAuthProviderEnum.kakao, user_info, user_type)
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    
    return OAuthCallbackResponse(
        access_token=access_token,
        user=user,
        is_new_user=user.oauth_provider == OAuthProviderEnum.kakao and user.oauth_id == user_info.get('id')
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = auth_header.split(" ")[1]
    from app.utils.auth import verify_token
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

@router.post("/logout")
async def logout():
    return {"message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."} 