"""
개선된 실제 데이터 수집 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from supabase import create_client

def preprocess_excel_data(df):
    """Excel 데이터 전처리"""
    # NaN 값 처리 및 타입 변환
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            # 무한대와 NaN 처리
            df[col] = df[col].replace([np.inf, -np.inf], 0)
            df[col] = df[col].fillna(0)
            df[col] = df[col].astype(float)
        elif df[col].dtype == 'object':
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str)

    return df

def test_improved_collection():
    """개선된 데이터 수집 테스트"""
    try:
        print("🔄 개선된 데이터 수집 테스트 시작...")

        # Supabase 클라이언트
        client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

        # 1. 엑셀 공급사 정보 조회
        supplier_result = client.table('suppliers').select('*').eq('code', 'excel_supplier').execute()
        if not supplier_result.data:
            print("❌ 엑셀 공급사를 찾을 수 없습니다.")
            return False

        supplier = supplier_result.data[0]
        print(f"✅ 공급사 조회 성공: {supplier['name']}")

        # 2. Excel 파일 로드 및 전처리
        print("📊 Excel 파일 로드 중...")
        df = pd.read_excel('data/test.xlsx')
        df = preprocess_excel_data(df)
        print(f"✅ 파일 로드 완료: {len(df)}개 행")

        # 3. 수집 작업 생성
        job_data = {
            'supplier_id': supplier['id'],
            'job_type': 'excel',
            'job_name': '실제 데이터 수집 테스트',
            'status': 'running',
            'total_items': len(df),
            'started_at': datetime.now().isoformat()
        }

        job_result = client.table('collection_jobs').insert(job_data).execute()
        job_id = job_result.data[0]['id']
        print(f"✅ 수집 작업 생성: {job_id}")

        # 4. 원본 데이터 저장 (테스트로 5개만)
        raw_products = []
        success_count = 0

        for i, (idx, row) in enumerate(df.head(5).iterrows()):
            try:
                # 안전한 데이터 변환
                raw_data = {}
                for key, value in row.items():
                    if pd.isna(value) or value == 'nan':
                        raw_data[key] = None
                    elif isinstance(value, (int, float)) and (np.isnan(value) or np.isinf(value)):
                        raw_data[key] = 0
                    else:
                        raw_data[key] = value

                raw_product = {
                    'supplier_id': supplier['id'],
                    'raw_data': raw_data,
                    'collection_method': 'excel',
                    'collection_source': 'data/test.xlsx',
                    'supplier_product_id': str(raw_data.get('상품코드(번호)', f'PRODUCT_{i}')),
                    'metadata': {
                        'row_index': int(idx),
                        'collected_at': datetime.now().isoformat()
                    }
                }
                raw_products.append(raw_product)
                success_count += 1

            except Exception as e:
                print(f"⚠️ 행 {i} 처리 실패: {e}")

        # 5. 원본 데이터 저장
        if raw_products:
            insert_result = client.table('raw_product_data').insert(raw_products).execute()
            saved_count = len(insert_result.data)
            print(f"✅ 원본 데이터 저장 완료: {saved_count}개 상품")
        else:
            print("❌ 저장할 데이터가 없습니다.")
            return False

        # 6. 작업 완료 업데이트
        client.table('collection_jobs').update({
            'status': 'completed',
            'collected_items': success_count,
            'completed_at': datetime.now().isoformat(),
            'result': {
                'total_processed': len(df),
                'success_count': success_count,
                'saved_count': len(raw_products)
            }
        }).eq('id', job_id).execute()

        print("🎉 데이터 수집 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_improved_collection()
    sys.exit(0 if success else 1)
