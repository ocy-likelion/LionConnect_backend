from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.core.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET,
    OAUTH_REDIRECT_URL
)
from app.models.user import User, OAuthProviderEnum, UserTypeEnum
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

# OAuth 설정
config = Config('.env')
oauth = OAuth(config)

# Google OAuth 설정
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Kakao OAuth 설정
oauth.register(
    name='kakao',
    client_id=KAKAO_CLIENT_ID,
    client_secret=KAKAO_CLIENT_SECRET,
    access_token_url='https://kauth.kakao.com/oauth/token',
    access_token_params=None,
    authorize_url='https://kauth.kakao.com/oauth/authorize',
    authorize_params=None,
    api_base_url='https://kapi.kakao.com/',
    client_kwargs={
        'scope': 'profile_nickname profile_image account_email'
    }
)

def get_or_create_user(db: Session, oauth_provider: OAuthProviderEnum, 
                      oauth_data: Dict[str, Any], user_type: UserTypeEnum = UserTypeEnum.student) -> User:
    """
    OAuth 데이터로 사용자를 찾거나 생성합니다.
    """
    oauth_id = str(oauth_data.get('id'))
    email = oauth_data.get('email')
    name = oauth_data.get('name', oauth_data.get('nickname', ''))
    profile_image = oauth_data.get('picture', oauth_data.get('profile_image_url', ''))
    
    # OAuth ID로 기존 사용자 찾기
    user = db.query(User).filter(
        User.oauth_provider == oauth_provider,
        User.oauth_id == oauth_id
    ).first()
    
    if user:
        # 기존 사용자 정보 업데이트
        user.name = name
        user.profile_image = profile_image
        user.email = email or user.email
        db.commit()
        return user
    
    # 이메일로 기존 사용자 찾기 (OAuth 계정 연결)
    if email:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            # 기존 계정에 OAuth 정보 연결
            existing_user.oauth_provider = oauth_provider
            existing_user.oauth_id = oauth_id
            existing_user.name = name
            existing_user.profile_image = profile_image
            db.commit()
            return existing_user
    
    # 새 사용자 생성
    new_user = User(
        email=email,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        name=name,
        profile_image=profile_image,
        user_type=user_type
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_google_user_info(token: Dict[str, Any]) -> Dict[str, Any]:
    """
    Google OAuth 토큰에서 사용자 정보를 추출합니다.
    """
    user_info = token.get('userinfo', {})
    return {
        'id': user_info.get('sub'),
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture')
    }

def get_kakao_user_info(token: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kakao OAuth 토큰에서 사용자 정보를 추출합니다.
    """
    # Kakao API에서 사용자 정보 가져오기
    resp = oauth.kakao.get('v2/user/me', token=token)
    user_info = resp.json()
    
    account = user_info.get('kakao_account', {})
    profile = account.get('profile', {})
    
    return {
        'id': str(user_info.get('id')),
        'email': account.get('email'),
        'name': profile.get('nickname'),
        'profile_image_url': profile.get('profile_image_url')
    } 