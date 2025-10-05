"""
Supabase 클라이언트 래퍼
비동기 및 동기 클라이언트 관리
"""

import asyncio
from typing import Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from loguru import logger

from src.config import settings


class SupabaseClient:
    """Supabase 클라이언트 싱글톤"""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None
    _service_client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """클라이언트 초기화"""
        if not self._client:
            self._initialize_clients()

    def _initialize_clients(self):
        """동기 및 서비스 클라이언트 초기화"""
        try:
            # 일반 클라이언트 (anon key)
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
                options=ClientOptions(
                    auto_refresh_token=True,
                    persist_session=True,
                ),
            )
            logger.info("Supabase client initialized successfully")

            # 서비스 클라이언트 (service key - RLS 우회)
            if settings.SUPABASE_SERVICE_KEY:
                self._service_client = create_client(
                    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
                )
                logger.info("Supabase service client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            raise

    @property
    def client(self) -> Client:
        """일반 클라이언트 반환 (RLS 적용)"""
        if not self._client:
            self._initialize_clients()
        return self._client

    @property
    def service_client(self) -> Optional[Client]:
        """서비스 클라이언트 반환 (RLS 우회)"""
        return self._service_client

    def get_table(self, table_name: str, use_service_key: bool = False):
        """테이블 참조 반환"""
        client = self._service_client if use_service_key else self._client
        if not client:
            raise ValueError("Supabase client not initialized")
        return client.table(table_name)

    def get_storage(self, use_service_key: bool = False):
        """Storage 참조 반환"""
        client = self._service_client if use_service_key else self._client
        if not client:
            raise ValueError("Supabase client not initialized")
        return client.storage

    def get_realtime(self):
        """Realtime 채널 반환"""
        if not self._client:
            raise ValueError("Supabase client not initialized")
        return self._client.realtime


class AsyncSupabaseClient:
    """비동기 Supabase 클라이언트"""

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.service_key = settings.SUPABASE_SERVICE_KEY
        self._client = None
        self._service_client = None

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self._close()

    async def _initialize(self):
        """비동기 클라이언트 초기화"""
        from supabase import acreate_client

        try:
            self._client = await acreate_client(self.url, self.key)
            logger.info("Async Supabase client initialized")

            if self.service_key:
                self._service_client = await acreate_client(
                    self.url, self.service_key
                )
                logger.info("Async Supabase service client initialized")

        except Exception as e:
            logger.error(f"Failed to initialize async clients: {e}")
            raise

    async def _close(self):
        """클라이언트 종료"""
        # 필요 시 정리 작업
        logger.info("Async Supabase client closed")

    @property
    def client(self):
        """비동기 클라이언트 반환"""
        if not self._client:
            raise ValueError("Async client not initialized. Use 'async with' context.")
        return self._client

    @property
    def service_client(self):
        """비동기 서비스 클라이언트 반환"""
        return self._service_client

    async def batch_insert(
        self,
        table_name: str,
        data: list[dict],
        chunk_size: int = 500,
        use_service_key: bool = False,
    ) -> dict:
        """
        배치 삽입 (청킹)

        Args:
            table_name: 테이블 이름
            data: 삽입할 데이터 리스트
            chunk_size: 청크 크기 (기본 500)
            use_service_key: 서비스 키 사용 여부

        Returns:
            삽입 결과 통계
        """
        client = self._service_client if use_service_key else self._client

        if not client:
            raise ValueError("Client not initialized")

        total = len(data)
        success_count = 0
        failed_count = 0
        errors = []

        # 청크 단위로 분할
        for i in range(0, total, chunk_size):
            chunk = data[i : i + chunk_size]

            try:
                response = await client.table(table_name).insert(chunk).execute()
                success_count += len(chunk)
                logger.info(
                    f"Inserted chunk {i//chunk_size + 1}: {len(chunk)} records"
                )

            except Exception as e:
                failed_count += len(chunk)
                error_msg = f"Chunk {i//chunk_size + 1} failed: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "errors": errors,
        }

    async def batch_upsert(
        self,
        table_name: str,
        data: list[dict],
        chunk_size: int = 500,
        on_conflict: str = "id",
        use_service_key: bool = False,
    ) -> dict:
        """
        배치 UPSERT (청킹)

        Args:
            table_name: 테이블 이름
            data: upsert할 데이터 리스트
            chunk_size: 청크 크기
            on_conflict: 충돌 시 기준 컬럼
            use_service_key: 서비스 키 사용 여부

        Returns:
            upsert 결과 통계
        """
        client = self._service_client if use_service_key else self._client

        if not client:
            raise ValueError("Client not initialized")

        total = len(data)
        success_count = 0
        failed_count = 0
        errors = []

        for i in range(0, total, chunk_size):
            chunk = data[i : i + chunk_size]

            try:
                response = (
                    await client.table(table_name)
                    .upsert(chunk, on_conflict=on_conflict, count="exact")
                    .execute()
                )
                success_count += len(chunk)
                logger.info(
                    f"Upserted chunk {i//chunk_size + 1}: {len(chunk)} records"
                )

            except Exception as e:
                failed_count += len(chunk)
                error_msg = f"Chunk {i//chunk_size + 1} failed: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "errors": errors,
        }


# 전역 동기 클라이언트 인스턴스
supabase_client = SupabaseClient()
