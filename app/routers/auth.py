from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import get_db, KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET, KAKAO_BACKEND_CALLBACK_URI, FRONTEND_REDIRECT_URI, FRONTEND_DEV_REDIRECT_URI
from app.models.user import User, UserTypeEnum, OAuthProviderEnum
from app.schemas.user import UserCreateStudent, UserCreateCompany, UserResponse, LoginRequest, TokenResponse
from app.schemas.auth import OAuthCallbackRequest, OAuthCallbackResponse
from app.utils.auth import create_access_token, verify_token
from app.utils.oauth import get_or_create_user, oauth
import httpx
import logging
from datetime import timedelta
import os

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ====== 기본 로그인/회원가입 ======
@router.post("/signup/student", response_model=UserResponse)
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
        user_type=UserTypeEnum.student,
        oauth_provider=None,
        oauth_id=None
    )
    new_user.set_password(user.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/signup/company", response_model=UserResponse)
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
        user_type=UserTypeEnum.company,
        oauth_provider=None,
        oauth_id=None
    )
    new_user.set_password(user.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    기본 로그인
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not user.check_password(request.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    return TokenResponse(access_token=access_token, user=user)

# ====== 카카오 OAuth 로그인 ======
@router.get("/login/kakao")
async def kakao_login(
    request: Request,
    user_type: UserTypeEnum = Query(UserTypeEnum.student, description="사용자 타입")
):
    """
    카카오 OAuth 로그인을 시작합니다
    """
    logger.info(f"🎯 카카오 로그인 시작 - user_type: {user_type}")
    
    # 카카오 OAuth가 설정되지 않은 경우
    if not hasattr(oauth, 'kakao'):
        logger.error("❌ 카카오 OAuth가 설정되지 않음")
        raise HTTPException(
            status_code=503, 
            detail="카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요."
        )
    
    # 백엔드 콜백 URI 사용 (카카오 개발자 콘솔에 등록된 URI)
    redirect_uri = KAKAO_BACKEND_CALLBACK_URI
    logger.info(f"🔗 Redirect URI: {redirect_uri}")
    
    return await oauth.kakao.authorize_redirect(
        request=request,
        redirect_uri=redirect_uri,
        scope="profile_nickname profile_image account_email",
        state=user_type.value
    )

@router.get("/callback/kakao")
async def kakao_callback_get(
    request: Request,
    code: str = Query(..., description="카카오에서 받은 인증 코드"),
    state: str = Query(..., description="사용자 타입"),
    db: Session = Depends(get_db)
):
    """
    카카오 OAuth 콜백을 처리하고 프론트엔드로 리다이렉트합니다.
    """
    logger.info("=" * 60)
    logger.info("🎯 카카오 인가코드 수신 확인")
    logger.info(f"📝 인가코드: {code}")
    logger.info(f"📏 인가코드 길이: {len(code)} 문자")
    logger.info(f"👤 사용자 타입: {state}")
    logger.info(f"🌐 요청 URL: {request.url}")
    logger.info("=" * 60)
    
    try:
        # OAuth 처리
        result = await _process_kakao_callback(code, state, db)
        
        # 환경에 따른 프론트엔드 리다이렉트 URI 결정
        is_production = os.environ.get('ENVIRONMENT', 'development') == 'production'
        frontend_uri = FRONTEND_REDIRECT_URI if is_production else FRONTEND_DEV_REDIRECT_URI
        
        # 프론트엔드로 리다이렉트 (토큰과 사용자 정보를 쿼리 파라미터로 전달)
        redirect_url = f"{frontend_uri}?access_token={result.access_token}&user_id={result.user.id}&user_type={result.user.user_type.value}&is_new_user={result.is_new_user}"
        
        logger.info(f"🔄 프론트엔드로 리다이렉트: {redirect_url}")
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"❌ 카카오 로그인 처리 중 오류: {str(e)}")
        # 오류 시 프론트엔드로 오류 정보와 함께 리다이렉트
        error_url = f"{FRONTEND_DEV_REDIRECT_URI}?error=login_failed&message={str(e)}"
        return RedirectResponse(url=error_url)

@router.post("/callback/kakao", response_model=OAuthCallbackResponse)
async def kakao_callback_post(
    callback_data: OAuthCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    카카오 OAuth 콜백을 처리합니다(POST 방식).
    """
    logger.info(f"📤 POST 카카오 콜백 시작 - code: {callback_data.code[:20]}..., user_type: {callback_data.user_type}")
    return await _process_kakao_callback(
        callback_data.code, 
        callback_data.user_type.value, 
        db
    )

async def _process_kakao_callback(code: str, state: str, db: Session):
    """
    카카오 OAuth 콜백 처리 공통 로직
    """
    logger.info(f"🔄 카카오 콜백 처리 시작 - state: {state}")
    
    # 카카오 OAuth가 설정되지 않은 경우
    if not hasattr(oauth, 'kakao'):
        logger.error("❌ 카카오 OAuth가 설정되지 않음")
        raise HTTPException(
            status_code=503, 
            detail="카카오 로그인이 현재 설정되지 않았습니다. 관리자에게 문의하세요."
        )
    
    try:
        # 사용자 타입 파싱
        logger.info(f"🔍 사용자 타입 파싱 시작 - state: {state}")
        user_type = UserTypeEnum(state)
        logger.info(f"✅ 사용자 타입 파싱 완료 - user_type: {user_type}")
    except ValueError as e:
        logger.warning(f"⚠️ 사용자 타입 파싱 실패, 기본값 사용 - error: {e}")
        user_type = UserTypeEnum.student
    
    try:
        # 1단계: 카카오 API에서 직접 액세스 토큰 획득
        logger.info("🔄 1단계: 카카오 토큰 교환 시작")
        token_data = await _exchange_kakao_code_for_token(code)
        logger.info("✅ 1단계: 카카오 토큰 교환 완료")
        
        # 2단계: 사용자 정보 가져오기
        logger.info("🔄 2단계: 카카오 사용자 정보 조회 시작")
        user_info = await _get_kakao_user_info_direct(token_data['access_token'])
        logger.info(f"✅ 2단계: 카카오 사용자 정보 조회 완료 - user_id: {user_info.get('id')}, name: {user_info.get('name')}")
        
        # 3단계: 사용자 찾기 또는 생성
        logger.info("🔄 3단계: 사용자 DB 처리 시작")
        user = get_or_create_user(db, OAuthProviderEnum.kakao, user_info, user_type)
        logger.info(f"✅ 3단계: 사용자 DB 처리 완료 - user_id: {user.id}")
        
        # 4단계: JWT 토큰 생성
        logger.info("🔄 4단계: JWT 토큰 생성 시작")
        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type.value},
            expires_delta=timedelta(minutes=60*24)
        )
        logger.info("✅ 4단계: JWT 토큰 생성 완료")
        
        logger.info("🎉 카카오 로그인 전체 프로세스 완료")
        return OAuthCallbackResponse(
            access_token=access_token,
            user=user,
            is_new_user=user.oauth_provider == OAuthProviderEnum.kakao and user.oauth_id == user_info.get('id')
        )
    
    except Exception as e:
        logger.error(f"❌ 카카오 로그인 처리 중 오류 발생: {str(e)}")
        logger.error(f"🔍 오류 타입: {type(e).__name__}")
        import traceback
        logger.error(f"📋 전체 스택트레이스:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"카카오 로그인 처리 중 오류가 발생했습니다: {str(e)}"
        )

async def _exchange_kakao_code_for_token(code: str):
    """
    카카오 인가 코드를 액세스 토큰으로 교환
    """
    logger.info("🔄 카카오 코드-토큰 교환 시작")
    
    try:
        logger.info(f"🔍 환경변수 확인 - KAKAO_CLIENT_ID: {KAKAO_CLIENT_ID}")
        logger.info(f"🔍 환경변수 확인 - KAKAO_CLIENT_SECRET: {'*' * len(str(KAKAO_CLIENT_SECRET)) if KAKAO_CLIENT_SECRET else 'None'}")
        
        token_url = "https://kauth.kakao.com/oauth/token"
        # 백엔드 콜백 URI 사용 (카카오 개발자 콘솔에 등록된 URI와 일치해야 함)
        redirect_uri = KAKAO_BACKEND_CALLBACK_URI
        
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "code": code
        }
        
        logger.info(f"📤 카카오 토큰 요청 데이터: grant_type={data['grant_type']}, client_id={data['client_id']}, redirect_uri={data['redirect_uri']}, code={code[:20]}...")
        
        async with httpx.AsyncClient() as client:
            logger.info(f"🌐 카카오 API 호출 시작 - URL: {token_url}")
            response = await client.post(token_url, data=data)
            logger.info(f"📥 카카오 API 응답 상태: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ 카카오 토큰 교환 실패 - 상태코드: {response.status_code}")
                logger.error(f"❌ 카카오 응답 내용: {response.text}")
                response.raise_for_status()
            
            token_data = response.json()
            logger.info("✅ 카카오 토큰 교환 성공!")
            logger.info(f"🎉 받은 토큰 정보: access_token={token_data.get('access_token', '')[:20]}..., token_type={token_data.get('token_type', 'N/A')}")
            return token_data
            
    except Exception as e:
        logger.error(f"❌ 카카오 토큰 교환 에러: {str(e)}")
        raise

async def _get_kakao_user_info_direct(access_token: str):
    """
    카카오 액세스 토큰으로 사용자 정보 조회
    """
    logger.info("🔄 카카오 사용자 정보 조회 시작")
    
    try:
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token[:20]}..."
        }
        
        logger.info(f"🌐 카카오 사용자 정보 API 호출 - URL: {user_info_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
            logger.info(f"📥 카카오 사용자 정보 응답 상태: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ 카카오 사용자 정보 조회 실패 - 상태코드: {response.status_code}")
                logger.error(f"❌ 카카오 응답 내용: {response.text}")
                response.raise_for_status()
            
            user_data = response.json()
            logger.info(f"📋 카카오 사용자 원본 데이터: {user_data}")
            
            account = user_data.get('kakao_account', {})
            profile = account.get('profile', {})
            
            result = {
                'id': str(user_data.get('id')),
                'email': account.get('email'),
                'name': profile.get('nickname'),
                'profile_image_url': profile.get('profile_image_url')
            }
            
            logger.info(f"✅ 카카오 사용자 정보 파싱 완료: {result}")
            return result
            
    except Exception as e:
        logger.error(f"❌ 카카오 사용자 정보 조회 중 에러: {str(e)}")
        raise

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
    """
    로그아웃 (클라이언트에서 토큰 삭제)
    """
    return {"message": "로그아웃되었습니다."}
