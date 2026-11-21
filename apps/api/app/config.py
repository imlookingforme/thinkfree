from typing import List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # API & Network
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return []

    # Security
    JWT_SECRET_KEY: str = "thinkfree_super_secret_jwt_signing_key_replace_for_production_32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    SESSION_COOKIE_NAME: str = "thinkfree_session"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./thinkfree.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Providers
    LLM_PROVIDER: str = "gemini"  # gemini | openai | mock
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Mail / SMTP Configuration (Gmail)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "raghuramvedantam16@gmail.com"
    SMTP_PASSWORD: str = "sfev qmku kjlp qphf"
    SMTP_FROM: str = "raghuramvedantam16@gmail.com"
    FRONTEND_URL: str = "https://thinkfree-v4fr.onrender.com"

    # Code Execution
    CODERUNNER_ADAPTER: str = "subprocess"  # subprocess | judge0
    JUDGE0_URL: str = "http://localhost:2358"

    # Speech & Bhashini ASR
    WHISPER_MODEL_SIZE: str = "base.en"
    AUDIO_RETENTION_DAYS: int = 30
    ALLOW_AUDIO_STORAGE: bool = True
    BHASHINI_API_KEY: Optional[str] = None
    BHASHINI_USER_ID: Optional[str] = None
    BHASHINI_PIPELINE_ENDPOINT: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    RESTRICT_TO_DOMAINS: Optional[str] = None

    # Effort Engine Defaults
    EFFORT_E_MIN: float = 0.35
    EFFORT_T_MIN_SECONDS: int = 180  # 3 minutes default


settings = Settings()
