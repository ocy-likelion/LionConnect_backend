from pydantic import BaseModel
from app.models.user import UserTypeEnum
from app.schemas.user import UserResponse

class OAuthCallbackRequest(BaseModel):
    """
    OAuth 콜백 요청 스키마 (POST 방식)
    """
    code: str
    user_type: UserTypeEnum

class OAuthCallbackResponse(BaseModel):
    """
    OAuth 콜백 응답 스키마
    """
    access_token: str
    user: UserResponse
    is_new_user: bool

    class Config:
        from_attributes = True 