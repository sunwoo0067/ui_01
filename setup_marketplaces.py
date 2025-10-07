"""
마켓플레이스 초기 설정 스크립트
5개 마켓플레이스를 Supabase에 등록합니다.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# 환경 변수 로드
load_dotenv()


def setup_marketplaces():
    """5개 마켓플레이스 등록"""
    try:
        print("🚀 마켓플레이스 등록 시작...\n")

        # Supabase 클라이언트 생성
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        # 마켓플레이스 정보 정의 (실제 테이블 스키마에 맞춤)
        marketplaces = [
            {
                'name': '쿠팡',
                'code': 'coupang',
                'type': 'api',
                'api_endpoint': 'https://api-gateway.coupang.com',
                'api_version': 'v2',
                'commission_rate': 10.0,
                'is_active': True
            },
            {
                'name': '네이버 스마트스토어',
                'code': 'naver_smartstore',
                'type': 'api',
                'api_endpoint': 'https://api.commerce.naver.com',
                'api_version': 'v1',
                'commission_rate': 5.0,
                'is_active': True
            },
            {
                'name': '11번가',
                'code': '11st',
                'type': 'api',
                'api_endpoint': 'https://openapi.11st.co.kr',
                'api_version': 'v1',
                'commission_rate': 9.0,
                'is_active': True
            },
            {
                'name': '지마켓',
                'code': 'gmarket',
                'type': 'api',
                'api_endpoint': 'https://api.gmarket.co.kr',
                'api_version': 'v1',
                'commission_rate': 10.0,
                'is_active': True
            },
            {
                'name': '옥션',
                'code': 'auction',
                'type': 'api',
                'api_endpoint': 'https://api.auction.co.kr',
                'api_version': 'v1',
                'commission_rate': 10.0,
                'is_active': True
            }
        ]

        # 기존 마켓플레이스 확인
        existing = client.table('sales_marketplaces').select('code').execute()
        existing_codes = {mp['code'] for mp in existing.data}

        # 마켓플레이스 등록
        registered_count = 0
        skipped_count = 0

        for mp in marketplaces:
            if mp['code'] in existing_codes:
                print(f"⏭️  {mp['name']} ({mp['code']}) - 이미 등록됨")
                skipped_count += 1
                continue

            result = client.table('sales_marketplaces').insert(mp).execute()
            
            if result.data:
                print(f"✅ {mp['name']} ({mp['code']}) - 등록 완료")
                print(f"   수수료율: {mp['commission_rate']}%")
                print(f"   API URL: {mp['api_endpoint']}")
                registered_count += 1
            else:
                print(f"❌ {mp['name']} - 등록 실패")

        print(f"\n📊 등록 결과:")
        print(f"   신규 등록: {registered_count}개")
        print(f"   기존 존재: {skipped_count}개")
        print(f"   총 마켓플레이스: {len(marketplaces)}개")

        # 전체 마켓플레이스 목록 확인
        all_marketplaces = client.table('sales_marketplaces').select('*').execute()
        print(f"\n🏪 전체 등록된 마켓플레이스: {len(all_marketplaces.data)}개")
        for mp in all_marketplaces.data:
            status = "🟢" if mp['is_active'] else "🔴"
            print(f"   {status} {mp['name']} ({mp['code']}) - 수수료 {mp['commission_rate']}%")

        print("\n🎉 마켓플레이스 설정 완료!")
        return True

    except Exception as e:
        print(f"\n❌ 마켓플레이스 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = setup_marketplaces()
    exit(0 if success else 1)
