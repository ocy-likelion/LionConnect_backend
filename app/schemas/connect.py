from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ConnectRequestCreate(BaseModel):
    user_id: int = Field(..., description="수료생 사용자 ID")
    company_representative_name: str = Field(..., description="기업담당자 이름")
    company_representative_email: str = Field(..., description="기업담당자 이메일")
    company_representative_phone: str = Field(..., description="기업담당자 전화번호")
    company_name: Optional[str] = Field(None, description="기업명")
    message: Optional[str] = Field(None, description="커넥트 요청 메시지")
    position: Optional[str] = Field(None, description="채용 포지션")
    job_description: Optional[str] = Field(None, description="직무 설명")
    required_stack: Optional[str] = Field(None, description="필수 기술 스택")
    career_level: Optional[str] = Field(None, description="희망 경력 수준")
    employment_type: Optional[str] = Field(None, description="고용 형태")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "company_representative_name": "김기업",
                "company_representative_email": "kim@company.com",
                "company_representative_phone": "010-1234-5678",
                "company_name": "테크컴퍼니",
                "message": "안녕하세요! 귀하의 포트폴리오를 보고 연락드립니다.",
                "position": "프론트엔드 개발자",
                "job_description": "React 기반 웹앱 개발",
                "required_stack": "React, TypeScript",
                "career_level": "신입~3년",
                "employment_type": "정규직"
            }
        }
    )

class ConnectRequestResponse(BaseModel):
    id: int
    company_user_id: Optional[int] = Field(None, description="기업 사용자 ID (로그인 시에만)")
    user_id: int = Field(..., description="수료생 사용자 ID")
    portfolio_id: Optional[int] = Field(None, description="포트폴리오 ID")
    company_representative_name: str
    company_representative_email: str
    company_representative_phone: str
    company_name: Optional[str]
    message: Optional[str]
    position: Optional[str]
    job_description: Optional[str]
    required_stack: Optional[str]
    career_level: Optional[str]
    employment_type: Optional[str]
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "company_user_id": None,
                "user_id": 1,
                "portfolio_id": 1,
                "company_representative_name": "김기업",
                "company_representative_email": "kim@company.com",
                "company_representative_phone": "010-1234-5678",
                "company_name": "테크컴퍼니",
                "message": "안녕하세요! 귀하의 포트폴리오를 보고 연락드립니다.",
                "position": "프론트엔드 개발자",
                "job_description": "React 기반 웹앱 개발",
                "required_stack": "React, TypeScript",
                "career_level": "신입~3년",
                "employment_type": "정규직",
                "created_at": "2024-07-01T12:00:00"
            }
        }
    ) 