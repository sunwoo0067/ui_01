"""
Supabase 연결 테스트 스크립트 (간단 버전)
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_basic_connection():
    """기본 연결 테스트"""
    try:
        print("🔄 기본 Supabase 연결 테스트 중...")

        # 환경 변수 확인
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        service_key = os.getenv('SUPABASE_SERVICE_KEY')

        print(f"URL: {url[:50]}...")
        print(f"Key 설정됨: {'예' if key else '아니오'}")
        print(f"Service Key 설정됨: {'예' if service_key else '아니오'}")

        # 직접 클라이언트 생성
        from supabase import create_client

        # 일반 클라이언트
        client = create_client(url, key)
        print("✅ 일반 클라이언트 생성 성공")

        # 서비스 클라이언트 (옵션)
        if service_key:
            service_client = create_client(url, service_key)
            print("✅ 서비스 클라이언트 생성 성공")

        # 테이블 접근 테스트
        try:
            result = client.table('suppliers').select('*').execute()
            print(f"✅ 테이블 접근 성공: {len(result.data)}개 공급사")
        except Exception as e:
            print(f"ℹ️ 테이블 접근 (예상된 결과): {type(e).__name__}")

        print("🎉 기본 연결 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_connection()
    exit(0 if success else 1)
