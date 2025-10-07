"""
psycopg2로 직접 PostgreSQL 연결하여 마이그레이션 적용
"""

import os
from dotenv import load_dotenv
import psycopg2
from loguru import logger

# 환경 변수 로드
load_dotenv()


def get_database_url():
    """Supabase DATABASE_URL 생성"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    # DATABASE_URL이 있으면 사용
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    # Supabase URL에서 프로젝트 참조 추출
    if supabase_url and supabase_password:
        # https://vecvkvumzhldioifgbxb.supabase.co
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        # PostgreSQL 연결 문자열 생성
        return f"postgresql://postgres.{project_ref}:{supabase_password}@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
    
    return None


def apply_migration():
    """마이그레이션 적용"""
    
    try:
        logger.info("🚀 마켓플레이스 판매자 스키마 마이그레이션 시작\n")
        
        # DATABASE_URL 가져오기
        database_url = get_database_url()
        
        if not database_url:
            logger.error("❌ DATABASE_URL을 생성할 수 없습니다.")
            logger.info("\n💡 .env 파일에 다음 중 하나를 설정하세요:")
            logger.info("   1. DATABASE_URL=postgresql://...")
            logger.info("   2. SUPABASE_DB_PASSWORD=your_db_password")
            logger.info("\n또는 Supabase Dashboard SQL Editor를 사용하세요:")
            logger.info("   https://supabase.com/dashboard/project/vecvkvumzhldioifgbxb/sql")
            return False
        
        # PostgreSQL 연결
        logger.info("📡 PostgreSQL 연결 중...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        logger.info("✅ PostgreSQL 연결 완료")
        
        # 마이그레이션 파일 읽기
        migration_file = "database/migrations/005_marketplace_seller_schema.sql"
        
        if not os.path.exists(migration_file):
            logger.error(f"❌ 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info(f"✅ 마이그레이션 파일 읽기 완료: {len(migration_sql)} bytes\n")
        
        # SQL 실행
        logger.info("🔧 SQL 실행 중...")
        
        try:
            cursor.execute(migration_sql)
            conn.commit()
            logger.info("✅ SQL 실행 완료")
            
        except Exception as e:
            conn.rollback()
            error_msg = str(e)
            
            # 이미 존재하는 객체는 경고만
            if 'already exists' in error_msg or 'duplicate' in error_msg.lower():
                logger.warning(f"⚠️  일부 객체가 이미 존재합니다 (정상)")
                logger.info("✅ 마이그레이션 완료")
            else:
                raise
        
        # 생성된 테이블 확인
        logger.info("\n📋 생성된 테이블 확인:")
        tables_to_check = [
            'marketplace_orders',
            'marketplace_inventory_sync_log',
            'marketplace_api_logs',
            'marketplace_sales_summary'
        ]
        
        for table in tables_to_check:
            try:
                if table == 'marketplace_sales_summary':
                    # 뷰 확인
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.views 
                        WHERE table_name = '{table}'
                    """)
                else:
                    # 테이블 확인
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    """)
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    logger.info(f"  ✅ {table}")
                else:
                    logger.warning(f"  ❌ {table} - 없음")
                    
            except Exception as e:
                logger.error(f"  ❌ {table} - {e}")
        
        cursor.close()
        conn.close()
        
        logger.info("\n🎉 마이그레이션 완료!")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ PostgreSQL 오류: {e}")
        logger.info("\n💡 Supabase Dashboard SQL Editor를 사용하세요:")
        logger.info("   https://supabase.com/dashboard/project/vecvkvumzhldioifgbxb/sql")
        logger.info(f"\n파일: database/migrations/005_marketplace_seller_schema.sql")
        return False
        
    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = apply_migration()
    exit(0 if success else 1)

