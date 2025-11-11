from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: str | None = Field(None, alias="SUPABASE_JWT_SECRET")
    database_url: str | None = Field(None, alias="DATABASE_URL")

    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")  # Deprecated, kept for backward compatibility
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    cors_origins: str | None = Field("*", alias="CORS_ORIGINS")
    log_level: str | None = Field("info", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()  # type: ignore[call-arg]


