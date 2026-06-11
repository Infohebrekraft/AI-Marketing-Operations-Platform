from pydantic import BaseModel, EmailStr
from typing import Any


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = ''
    password: str
    organization_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class BrandProfileIn(BaseModel):
    company_name: str
    industry: str = ''
    target_audience: str = ''
    services: str = ''
    brand_voice: str = 'professional, executive-friendly, clear'
    brand_colors: str = '#0B1220,#1F6FEB,#FFFFFF'
    positioning_statement: str = ''
    topics_to_focus: list[str] = []
    topics_to_avoid: list[str] = []
    preferred_hashtags: list[str] = []
    forbidden_words: list[str] = []
    default_post_time: str = '09:00'
    timezone: str = 'Asia/Dubai'


class GeneratePostRequest(BaseModel):
    organization_id: int
    topic: str
    extra_focus: list[str] = []
    extra_avoid: list[str] = []
    auto_save: bool = True


class SchedulePostRequest(BaseModel):
    post_id: int
    scheduled_time: str


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    image_title: str = ''
    image_subtitle: str = ''
    topic: str = ''
    status: str
    scheduled_time: str = ''
    ai_metadata: dict[str, Any] = {}

    class Config:
        from_attributes = True
