from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, TokenResponse, OAuthLoginRequest, OAuthCallbackResponse, OAuthCallbackRequest, LoginRequest, UserCreateStudent, UserCreateCompany, UserTypeEnum
from app.models.user import User, StudentProfile, CompanyProfile, OAuthProviderEnum
from app.core.config import SessionLocal, KAKAO_REDIRECT_URI, KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.oauth import oauth, get_or_create_user, get_kakao_user_info_async
from datetime import timedelta
from typing import Optional
import httpx
import logging

# 로거 ?�정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ====== 기존 ?�원가??로그??API ======
@router.post("/signup/student", response_model=UserResponse)
def signup_student(user: UserCreateStudent, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="?��? ?�용 중인 ?�메?�입?�다.")
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
        raise HTTPException(status_code=400, detail="?��? ?�용 중인 ?�메?�입?�다.")
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
        raise HTTPException(status_code=401, detail="?�메???�는 비�?번호가 ?�바르�? ?�습?�다.")
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": user.user_type.value},
        expires_delta=timedelta(minutes=60*24)
    )
    return TokenResponse(access_token=access_token, user=user)

# ====== 카카??OAuth 로그???�드?�인??======
@router.get("/login/kakao")
async def kakao_login(
    request: Request,
    user_type: UserTypeEnum = Query(UserTypeEnum.student, description="?�용???�형")
):
    """
    카카??OAuth 로그?�을 ?�작?�니??
    """
    logger.info(f"?? 카카??로그???�작 - user_type: {user_type}")
    
    # 카카??OAuth가 ?�정?��? ?��? 경우
    if not hasattr(oauth, 'kakao'):
        logger.error("??카카??OAuth가 ?�정?��? ?�음")
        raise HTTPException(
            status_code=503, 
            detail="카카??로그?�이 ?�재 ?�정?��? ?�았?�니?? 관리자?�게 문의?�세??"
        )
    
    redirect_uri = KAKAO_REDIRECT_URI
    logger.info(f"?�� Redirect URI: {redirect_uri}")
    
    return await oauth.kakao.authorize_redirect(
        request=request,
        redirect_uri=redirect_uri,
        scope="profile_nickname profile_image account_email",
        state=user_type.value
    )

@router.get("/callback/kakao", response_model=OAuthCallbackResponse)
async def kakao_callback_get(
    request: Request,
    code: str = Query(..., description="카카?�에??받�? ?�증 코드"),
    state: str = Query(..., description="?�용???�형"),
    db: Session = Depends(get_db)
):
    """
    카카??OAuth 콜백??처리?�니??(GET 방식).
    logger.info("=" * 50)
    logger.info(" GET īī�� �ݹ� ����")
    logger.info(f" ���� �ΰ��ڵ�: {code}")
    logger.info(f" ���� �ڵ� ����: {len(code)} ����")
    logger.info(f" ���� state: {state}")
    logger.info(f" ��û URL: {request.url}")
    logger.info(f" ��û ���: {dict(request.headers)}")
    logger.info("=" * 50)
):
    """
    카카??OAuth 콜백??처리?�니??(POST 방식).
    """
    logger.info(f"?�� POST 카카??콜백 ?�작 - code: {callback_data.code[:20]}..., user_type: {callback_data.user_type}")
    return await _process_kakao_callback(
        callback_data.code, 
        callback_data.user_type.value, 
        db
    )

async def _process_kakao_callback(code: str, state: str, db: Session):
    """
    카카??OAuth 콜백 처리 공통 로직
    """
    logger.info(f"?�️ 카카??콜백 처리 ?�작 - state: {state}")
    
    # 카카??OAuth가 ?�정?��? ?��? 경우
    if not hasattr(oauth, 'kakao'):
        logger.error("??카카??OAuth가 ?�정?��? ?�음")
        raise HTTPException(
            status_code=503, 
            detail="카카??로그?�이 ?�재 ?�정?��? ?�았?�니?? 관리자?�게 문의?�세??"
        )
    
    try:
        # ?�용???�형 ?�싱
        logger.info(f"?�� ?�용???�형 ?�싱 �?- state: {state}")
        user_type = UserTypeEnum(state)
        logger.info(f"???�용???�형 ?�싱 ?�료 - user_type: {user_type}")
    except ValueError as e:
        logger.warning(f"?�️ ?�용???�형 ?�싱 ?�패, 기본�??�용 - error: {e}")
        user_type = UserTypeEnum.student
    
    try:
        # 1?�계: 카카??API?�서 직접 ?�세???�큰 ?�득
        logger.info("?�� 1?�계: 카카???�큰 교환 ?�작")
        token_data = await _exchange_kakao_code_for_token(code)
        logger.info("??1?�계: 카카???�큰 교환 ?�료")
        
        # 2?�계: ?�용???�보 가?�오�?
        logger.info("?�� 2?�계: 카카???�용???�보 조회 ?�작")
        user_info = await _get_kakao_user_info_direct(token_data['access_token'])
        logger.info(f"??2?�계: 카카???�용???�보 조회 ?�료 - user_id: {user_info.get('id')}, name: {user_info.get('name')}")
        
        # 3?�계: ?�용??찾기 ?�는 ?�성
        logger.info("?�� 3?�계: ?�용??DB 처리 ?�작")
        user = get_or_create_user(db, OAuthProviderEnum.kakao, user_info, user_type)
        logger.info(f"??3?�계: ?�용??DB 처리 ?�료 - user_id: {user.id}")
        
        # 4?�계: JWT ?�큰 ?�성
        logger.info("?�� 4?�계: JWT ?�큰 ?�성 ?�작")
        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type.value},
            expires_delta=timedelta(minutes=60*24)
        )
        logger.info("??4?�계: JWT ?�큰 ?�성 ?�료")
        
        logger.info("?�� 카카??로그???�체 ?�로?�스 ?�료")
        return OAuthCallbackResponse(
            access_token=access_token,
            user=user,
            is_new_user=user.oauth_provider == OAuthProviderEnum.kakao and user.oauth_id == user_info.get('id')
        )
    
    except Exception as e:
        logger.error(f"?�� 카카??로그??처리 �??�러 발생: {str(e)}")
        logger.error(f"?�� ?�러 ?�?? {type(e).__name__}")
        import traceback
        logger.error(f"?�� ?�체 ?�택?�레?�스:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"카카??로그??처리 �??�류가 발생?�습?�다: {str(e)}"
        )

async def _exchange_kakao_code_for_token(code: str):
    """
    카카???��? 코드�??�세???�큰?�로 교환
    """
    logger.info("?�� 카카??코드-?�큰 교환 ?�작")
    
    try:

        
        logger.info(f"?�� ?�경변???�인 - KAKAO_CLIENT_ID: {KAKAO_CLIENT_ID}")
        logger.info(f"?�� ?�경변???�인 - KAKAO_CLIENT_SECRET: {'*' * len(str(KAKAO_CLIENT_SECRET)) if KAKAO_CLIENT_SECRET else 'None'}")
        
        token_url = "https://kauth.kakao.com/oauth/token"
        redirect_uri = KAKAO_REDIRECT_URI
        
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "code": code
        }
        
        logger.info(f"?�� 카카???�큰 ?�청 ?�이?? grant_type={data['grant_type']}, client_id={data['client_id']}, redirect_uri={data['redirect_uri']}, code={code[:20]}...")
        
        async with httpx.AsyncClient() as client:
            logger.info(f"?�� 카카??API ?�출 ?�작 - URL: {token_url}")
            response = await client.post(token_url, data=data)
            logger.info(f"?�� 카카??API ?�답 ?�태: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"??카카???�큰 교환 ?�패 - ?�태코드: {response.status_code}")
                logger.error(f"??카카???�답 ?�용: {response.text}")
                response.raise_for_status()
            
            token_data = response.json()
            logger.info("??카카???�큰 교환 ?�공")
            return token_data
            
    except Exception as e:
        logger.error(f"?�� 카카???�큰 교환 �??�러: {str(e)}")
        raise

async def _get_kakao_user_info_direct(access_token: str):
    """
    카카???�세???�큰?�로 ?�용???�보 조회
    """
    logger.info("?�� 카카???�용???�보 조회 ?�작")
    
    try:
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token[:20]}..."
        }
        
        logger.info(f"?�� 카카???�용???�보 API ?�출 - URL: {user_info_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
            logger.info(f"?�� 카카???�용???�보 ?�답 ?�태: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"??카카???�용???�보 조회 ?�패 - ?�태코드: {response.status_code}")
                logger.error(f"??카카???�답 ?�용: {response.text}")
                response.raise_for_status()
            
            user_data = response.json()
            logger.info(f"?�� 카카???�용???�본 ?�이?? {user_data}")
            
            account = user_data.get('kakao_account', {})
            profile = account.get('profile', {})
            
            result = {
                'id': str(user_data.get('id')),
                'email': account.get('email'),
                'name': profile.get('nickname'),
                'profile_image_url': profile.get('profile_image_url')
            }
            
            logger.info(f"??카카???�용???�보 ?�싱 ?�료: {result}")
            return result
            
    except Exception as e:
        logger.error(f"?�� 카카???�용???�보 조회 �??�러: {str(e)}")
        raise

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="?�증 ?�큰???�요?�니??")
    token = auth_header.split(" ")[1]
    from app.utils.auth import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="?�효?��? ?��? ?�큰?�니??")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="?�큰???�용???�보가 ?�습?�다.")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="?�용?��? 찾을 ???�습?�다.")
    return user

@router.post("/logout")
async def logout():
    return {"message": "로그?�웃?�었?�니?? ?�라?�언?�에???�큰????��?�주?�요."}
