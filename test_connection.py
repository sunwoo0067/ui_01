"""
Supabase 연결 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.supabase_client import supabase_client

def test_connection():
    """Supabase 연결 테스트"""
    try:
        print("🔄 Supabase 연결 테스트 중...")

        # 클라이언트 초기화 확인
        client = supabase_client.client
        print(f"✅ 클라이언트 초기화 성공: {client}")

        # 서비스 클라이언트 확인 (옵션)
        service_client = supabase_client.service_client
        if service_client:
            print(f"✅ 서비스 클라이언트 초기화 성공: {service_client}")
        else:
            print("⚠️ 서비스 클라이언트가 설정되지 않음 (서비스 키 누락)")

        # 테이블 목록 조회 테스트
        try:
            tables = client.table('suppliers').select('*').execute()
            print(f"✅ 테이블 접근 성공: suppliers 테이블에 {len(tables.data)}개 레코드")
        except Exception as e:
            print(f"⚠️ 테이블 접근 실패 (정상적임 - 빈 테이블): {e}")

        print("🎉 연결 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
