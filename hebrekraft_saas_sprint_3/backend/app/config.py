from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'HebreKraft SaaS Sprint 3.0'
    environment: str = 'development'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 1440
    database_url: str = 'sqlite:///./hebrekraft.db'
    backend_base_url: str = 'http://localhost:8000'
    frontend_base_url: str = 'http://localhost:8501'

    gemini_api_key: str = ''
    openai_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    openai_model: str = 'gpt-4o-mini'

    linkedin_client_id: str = ''
    linkedin_client_secret: str = ''
    linkedin_redirect_uri: str = 'http://localhost:8000/api/linkedin/callback'
    linkedin_scopes: str = 'openid profile email w_member_social'
    linkedin_default_org_urn: str = ''

    fernet_key: str = ''
    timezone: str = 'Asia/Dubai'
    redis_url: str = 'redis://redis:6379/0'


@lru_cache
def get_settings() -> Settings:
    return Settings()
