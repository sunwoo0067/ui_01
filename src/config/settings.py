"""
설정 파일
환경 변수 및 앱 설정 관리
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Supabase 설정
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")

    # Context7 API (MCP)
    CONTEXT7_API_KEY: Optional[str] = os.getenv("CONTEXT7_API_KEY")

    # 배치 처리 설정
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "500"))
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "5"))

    # 이미지 처리 설정
    IMAGE_MAX_WIDTH: int = int(os.getenv("IMAGE_MAX_WIDTH", "1200"))
    IMAGE_MAX_HEIGHT: int = int(os.getenv("IMAGE_MAX_HEIGHT", "1200"))
    IMAGE_QUALITY: int = int(os.getenv("IMAGE_QUALITY", "85"))
    SUPPORTED_IMAGE_FORMATS: list[str] = ["jpg", "jpeg", "png", "webp"]

    # Storage 설정
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "product-images")

    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "logs/app.log")

    # OpenAI (임베딩 생성용)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    EMBEDDING_DIMENSION: int = 1536

    # Realtime 설정
    REALTIME_CHANNEL: str = os.getenv("REALTIME_CHANNEL", "upload-progress")

    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()
