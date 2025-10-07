"""
실제 데이터 수집 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from supabase import create_client

def test_data_collection():
    """실제 데이터 수집 테스트"""
    try:
        print("🔄 실제 데이터 수집 테스트 시작...")

        # Supabase 클라이언트
        client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

        # 1. 엑셀 공급사 정보 조회
        supplier_result = client.table('suppliers').select('*').eq('code', 'excel_supplier').execute()
        if not supplier_result.data:
            print("❌ 엑셀 공급사를 찾을 수 없습니다.")
            return False

        supplier = supplier_result.data[0]
        print(f"✅ 공급사 조회 성공: {supplier['name']}")

        # 2. 컬렉션 작업 생성 및 실행
        print("📊 데이터 수집을 시작합니다...")

        # 간단한 수집 작업 생성
        job_data = {
            'supplier_id': supplier['id'],
            'job_type': 'excel',
            'job_name': '테스트 데이터 수집',
            'config': {
                'file_path': 'data/test.xlsx',
                'limit': 10  # 테스트로 10개만
            }
        }

        job_result = client.table('collection_jobs').insert(job_data).execute()
        job_id = job_result.data[0]['id']
        print(f"✅ 수집 작업 생성: {job_id}")

        # 3. 실제 수집 작업 시뮬레이션
        print("🔄 Excel 파일에서 데이터를 읽는 중...")

        import pandas as pd
        df = pd.read_excel('data/test.xlsx')

        print(f"✅ Excel 파일 로드 완료: {len(df)}개 행")

        # 4. 원본 데이터 저장 (첫 10개만 테스트)
        raw_products = []
        for i, row in df.head(10).iterrows():
            raw_product = {
                'supplier_id': supplier['id'],
                'raw_data': row.to_dict(),
                'collection_method': 'excel',
                'collection_source': 'data/test.xlsx',
                'supplier_product_id': str(row.get('상품코드', f'PRODUCT_{i}'))
            }
            raw_products.append(raw_product)

        if raw_products:
            insert_result = client.table('raw_product_data').insert(raw_products).execute()
            collected_count = len(insert_result.data)
            print(f"✅ 원본 데이터 저장 완료: {collected_count}개 상품")

        # 5. 작업 완료 업데이트
        client.table('collection_jobs').update({
            'status': 'completed',
            'collected_items': len(raw_products),
            'total_items': len(df)
        }).eq('id', job_id).execute()

        print("🎉 데이터 수집 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_collection()
    sys.exit(0 if success else 1)
