"""
005_marketplace_seller_schema.sql 마이그레이션 적용
Supabase에 마켓플레이스 판매자 스키마 적용
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
from loguru import logger

# 환경 변수 로드
load_dotenv()


async def apply_migration():
    """마이그레이션 적용"""
    
    try:
        logger.info("🚀 마켓플레이스 판매자 스키마 마이그레이션 시작\n")
        
        # Supabase 클라이언트 생성 (service_role 키 사용)
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            logger.error("❌ SUPABASE_URL 또는 SUPABASE_SERVICE_KEY가 설정되지 않았습니다.")
            return False
        
        client = create_client(supabase_url, supabase_service_key)
        logger.info("✅ Supabase 클라이언트 생성 완료")
        
        # 마이그레이션 파일 읽기
        migration_file = "database/migrations/005_marketplace_seller_schema.sql"
        
        if not os.path.exists(migration_file):
            logger.error(f"❌ 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info(f"✅ 마이그레이션 파일 읽기 완료: {len(migration_sql)} bytes")
        
        # SQL을 여러 문장으로 분리 (세미콜론 기준)
        # 주석과 빈 줄 제거
        statements = []
        current_statement = []
        
        for line in migration_sql.split('\n'):
            # 주석 제거 (-- 로 시작)
            if line.strip().startswith('--'):
                continue
            
            current_statement.append(line)
            
            # 세미콜론으로 끝나면 하나의 statement 완성
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement:
                    statements.append(statement)
                current_statement = []
        
        logger.info(f"📝 실행할 SQL 문장: {len(statements)}개\n")
        
        # 각 statement 실행
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # CREATE, ALTER, COMMENT 문은 직접 실행
                logger.info(f"[{i}/{len(statements)}] 실행 중...")
                
                # Supabase Python 클라이언트로 직접 SQL 실행
                result = client.rpc('exec_sql', {'sql': statement}).execute()
                
                logger.info(f"  ✅ 성공")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                
                # 이미 존재하는 객체는 무시
                if 'already exists' in error_msg or 'duplicate' in error_msg.lower():
                    logger.warning(f"  ⏭️  이미 존재함 (건너뛰기)")
                    success_count += 1
                else:
                    logger.error(f"  ❌ 실패: {error_msg}")
                    error_count += 1
        
        # 결과 요약
        logger.info(f"\n📊 마이그레이션 결과:")
        logger.info(f"   성공: {success_count}개")
        logger.info(f"   실패: {error_count}개")
        logger.info(f"   총: {len(statements)}개")
        
        if error_count == 0:
            logger.info("\n🎉 마이그레이션 완료!")
            
            # 생성된 테이블 확인
            logger.info("\n📋 생성된 테이블 확인:")
            tables_to_check = [
                'marketplace_orders',
                'marketplace_inventory_sync_log',
                'marketplace_api_logs'
            ]
            
            for table in tables_to_check:
                try:
                    result = client.table(table).select('id').limit(1).execute()
                    logger.info(f"  ✅ {table} - 접근 가능")
                except Exception as e:
                    logger.warning(f"  ⚠️  {table} - {e}")
            
            return True
        else:
            logger.warning(f"\n⚠️  일부 실패가 있었습니다 ({error_count}개)")
            return False
            
    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    exit(0 if success else 1)

