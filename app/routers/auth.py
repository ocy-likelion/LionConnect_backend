from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, TokenResponse, OAuthLoginRequest, OAuthCallbackResponse
from app.models.user import User, StudentProfile, CompanyProfile, OAuthProviderEnum, UserTypeEnum
from app.core.config import SessionLocal
from app.utils.auth import create_access_token
from app.utils.oauth import oauth, get_or_create_user, get_google_user_info, get_kakao_user_info
from datetime import timedelta
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Google OAuth 로그인
@router.get(
    "/login/google",
    summary="Google 소셜 로그인 시작",
    description="""
    ## Google OAuth2 로그인을 시작합니다.
    
    ### 동작 과정
    1. 사용자를 Google OAuth 인증 페이지로 리디렉트
    2. Google에서 사용자 인증 및 권한 승인
    3. 인증 완료 후 `/auth/callback/google`로 리디렉트
    
    ### 쿼리 파라미터
    - `user_type`: 사용자 유형 (student/company) - 기본값: student
    
    ### 예시
    ```
    GET /auth/login/google?user_type=student
    ```
    
    ### 응답
    - **302 Redirect**: Google OAuth 인증 페이지로 리디렉트
    """,
    response_description="Google OAuth 인증 페이지로 리디렉트"
)
async def google_login(
    request: Request, 
    user_type: UserTypeEnum = Query(
        default=UserTypeEnum.student,
        description="사용자 유형 (student: 학생, company: 기업)"
    )
):
    """
    Google OAuth 로그인을 시작합니다.
    
    사용자를 Google OAuth 인증 페이지로 리디렉트하여 소셜 로그인을 진행합니다.
    인증이 완료되면 자동으로 콜백 URL로 리디렉트됩니다.
    """
    redirect_uri = str(request.url_for('google_callback'))
    return await oauth.google.authorize_redirect(
        request, 
        redirect_uri,
        access_type="offline",
        prompt="select_account"
    )

# Google OAuth 콜백
@router.get(
    "/callback/google", 
    response_model=OAuthCallbackResponse,
    summary="Google OAuth 콜백 처리",
    description="""
    ## Google OAuth 인증 완료 후 콜백을 처리합니다.
    
    ### 동작 과정
    1. Google에서 전달받은 인증 코드로 액세스 토큰 획득
    2. Google API를 통해 사용자 정보 조회
    3. 사용자 정보로 계정 생성 또는 기존 계정 조회
    4. JWT 토큰 생성 및 반환
    
    ### 응답 데이터
    - `access_token`: JWT 액세스 토큰 (24시간 유효)
    - `token_type`: 토큰 타입 (항상 "bearer")
    - `user`: 사용자 정보
    - `is_new_user`: 신규 사용자 여부
    
    ### 사용자 정보
    - `id`: 사용자 고유 ID
    - `email`: 이메일 주소
    - `name`: 사용자 이름
    - `user_type`: 사용자 유형 (student/company)
    - `oauth_provider`: OAuth 제공자 (google)
    - `profile_image`: 프로필 이미지 URL
    
    ### 에러 응답
    - `400 Bad Request`: OAuth 인증 실패
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "로그인 성공",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "name": "홍길동",
                            "user_type": "student",
                            "oauth_provider": "google",
                            "profile_image": "https://lh3.googleusercontent.com/...",
                            "created_at": "2024-01-01T00:00:00",
                            "updated_at": "2024-01-01T00:00:00"
                        },
                        "is_new_user": False
                    }
                }
            }
        },
        400: {
            "description": "OAuth 인증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Google 로그인 실패: 인증 코드가 유효하지 않습니다."
                    }
                }
            }
        }
    }
)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google OAuth 콜백을 처리합니다.
    
    Google에서 전달받은 인증 정보를 바탕으로 사용자 계정을 생성하거나
    기존 계정을 조회하여 JWT 토큰을 발급합니다.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = get_google_user_info(token)
        
        # 사용자 생성 또는 조회
        user = get_or_create_user(db, OAuthProviderEnum.google, user_info)
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type.value},
            expires_delta=timedelta(minutes=60*24)
        )
        
        return OAuthCallbackResponse(
            access_token=access_token,
            user=user,
            is_new_user=user.created_at == user.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google 로그인 실패: {str(e)}")

# Kakao OAuth 로그인
@router.get(
    "/login/kakao",
    summary="Kakao 소셜 로그인 시작",
    description="""
    ## Kakao OAuth2 로그인을 시작합니다.
    
    ### 동작 과정
    1. 사용자를 Kakao OAuth 인증 페이지로 리디렉트
    2. Kakao에서 사용자 인증 및 권한 승인
    3. 인증 완료 후 `/auth/callback/kakao`로 리디렉트
    
    ### 쿼리 파라미터
    - `user_type`: 사용자 유형 (student/company) - 기본값: student
    
    ### 예시
    ```
    GET /auth/login/kakao?user_type=company
    ```
    
    ### 응답
    - **302 Redirect**: Kakao OAuth 인증 페이지로 리디렉트
    """,
    response_description="Kakao OAuth 인증 페이지로 리디렉트"
)
async def kakao_login(
    request: Request, 
    user_type: UserTypeEnum = Query(
        default=UserTypeEnum.student,
        description="사용자 유형 (student: 학생, company: 기업)"
    )
):
    """
    Kakao OAuth 로그인을 시작합니다.
    
    사용자를 Kakao OAuth 인증 페이지로 리디렉트하여 소셜 로그인을 진행합니다.
    인증이 완료되면 자동으로 콜백 URL로 리디렉트됩니다.
    """
    redirect_uri = str(request.url_for('kakao_callback'))
    return await oauth.kakao.authorize_redirect(request, redirect_uri)

# Kakao OAuth 콜백
@router.get(
    "/callback/kakao", 
    response_model=OAuthCallbackResponse,
    summary="Kakao OAuth 콜백 처리",
    description="""
    ## Kakao OAuth 인증 완료 후 콜백을 처리합니다.
    
    ### 동작 과정
    1. Kakao에서 전달받은 인증 코드로 액세스 토큰 획득
    2. Kakao API를 통해 사용자 정보 조회
    3. 사용자 정보로 계정 생성 또는 기존 계정 조회
    4. JWT 토큰 생성 및 반환
    
    ### 응답 데이터
    - `access_token`: JWT 액세스 토큰 (24시간 유효)
    - `token_type`: 토큰 타입 (항상 "bearer")
    - `user`: 사용자 정보
    - `is_new_user`: 신규 사용자 여부
    
    ### 사용자 정보
    - `id`: 사용자 고유 ID
    - `email`: 이메일 주소 (Kakao 계정에 이메일이 있는 경우)
    - `name`: 사용자 닉네임
    - `user_type`: 사용자 유형 (student/company)
    - `oauth_provider`: OAuth 제공자 (kakao)
    - `profile_image`: 프로필 이미지 URL
    
    ### 에러 응답
    - `400 Bad Request`: OAuth 인증 실패
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "로그인 성공",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": 2,
                            "email": "user@kakao.com",
                            "name": "카카오사용자",
                            "user_type": "company",
                            "oauth_provider": "kakao",
                            "profile_image": "http://k.kakaocdn.net/...",
                            "created_at": "2024-01-01T00:00:00",
                            "updated_at": "2024-01-01T00:00:00"
                        },
                        "is_new_user": True
                    }
                }
            }
        },
        400: {
            "description": "OAuth 인증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Kakao 로그인 실패: 인증 코드가 유효하지 않습니다."
                    }
                }
            }
        }
    }
)
async def kakao_callback(request: Request, db: Session = Depends(get_db)):
    """
    Kakao OAuth 콜백을 처리합니다.
    
    Kakao에서 전달받은 인증 정보를 바탕으로 사용자 계정을 생성하거나
    기존 계정을 조회하여 JWT 토큰을 발급합니다.
    """
    try:
        token = await oauth.kakao.authorize_access_token(request)
        user_info = get_kakao_user_info(token)
        
        # 사용자 생성 또는 조회
        user = get_or_create_user(db, OAuthProviderEnum.kakao, user_info)
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type.value},
            expires_delta=timedelta(minutes=60*24)
        )
        
        return OAuthCallbackResponse(
            access_token=access_token,
            user=user,
            is_new_user=user.created_at == user.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kakao 로그인 실패: {str(e)}")

# 로그인 상태 확인
@router.get(
    "/me", 
    response_model=UserResponse,
    summary="현재 로그인한 사용자 정보 조회",
    description="""
    ## 현재 로그인한 사용자의 정보를 조회합니다.
    
    ### 인증 요구사항
    - Authorization 헤더에 Bearer 토큰 필요
    - 토큰 형식: `Bearer {access_token}`
    
    ### 동작 과정
    1. Authorization 헤더에서 JWT 토큰 추출
    2. 토큰 검증 및 디코딩
    3. 토큰의 사용자 ID로 데이터베이스 조회
    4. 사용자 정보 반환
    
    ### 응답 데이터
    - `id`: 사용자 고유 ID
    - `email`: 이메일 주소
    - `name`: 사용자 이름
    - `user_type`: 사용자 유형 (student/company)
    - `oauth_provider`: OAuth 제공자 (google/kakao)
    - `profile_image`: 프로필 이미지 URL
    - `created_at`: 계정 생성 시간
    - `updated_at`: 정보 수정 시간
    
    ### 에러 응답
    - `401 Unauthorized`: 토큰이 없거나 유효하지 않음
    - `404 Not Found`: 사용자를 찾을 수 없음
    """,
    responses={
        200: {
            "description": "사용자 정보 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "user@example.com",
                        "name": "홍길동",
                        "user_type": "student",
                        "oauth_provider": "google",
                        "profile_image": "https://lh3.googleusercontent.com/...",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00"
                    }
                }
            }
        },
        401: {
            "description": "인증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "인증 토큰이 필요합니다."
                    }
                }
            }
        },
        404: {
            "description": "사용자를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "사용자를 찾을 수 없습니다."
                    }
                }
            }
        }
    }
)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자 정보를 반환합니다.
    
    Authorization 헤더의 Bearer 토큰을 검증하여
    현재 로그인한 사용자의 상세 정보를 반환합니다.
    """
    # Authorization 헤더에서 토큰 추출
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

# 로그아웃 (클라이언트에서 토큰 삭제)
@router.post(
    "/logout",
    summary="로그아웃",
    description="""
    ## 로그아웃을 수행합니다.
    
    ### 동작 과정
    1. 클라이언트에서 저장된 JWT 토큰 삭제
    2. 서버에서는 별도 처리가 없음 (JWT는 무상태)
    
    ### 클라이언트 처리사항
    - localStorage/sessionStorage에서 토큰 삭제
    - 쿠키에서 토큰 삭제
    - 로그인 페이지로 리디렉트
    
    ### 예시
    ```javascript
    // 클라이언트에서 토큰 삭제
    localStorage.removeItem('access_token');
    // 또는
    sessionStorage.removeItem('access_token');
    ```
    
    ### 응답
    - `200 OK`: 로그아웃 성공 메시지
    """,
    responses={
        200: {
            "description": "로그아웃 성공",
            "content": {
                "application/json": {
                    "example": {
                        "message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."
                    }
                }
            }
        }
    }
)
async def logout():
    """
    로그아웃합니다. (클라이언트에서 토큰을 삭제해야 합니다.)
    
    JWT는 무상태 토큰이므로 서버에서는 별도 처리가 없습니다.
    클라이언트에서 저장된 토큰을 삭제하여 로그아웃을 완료합니다.
    """
    return {"message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."} 