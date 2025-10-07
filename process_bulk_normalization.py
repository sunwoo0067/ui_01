#!/usr/bin/env python3
"""
대량 데이터 정규화 처리 (최적화)
65,000개 이상의 데이터를 효율적으로 정규화
"""

import asyncio
import json
from datetime import datetime
from uuid import UUID
from loguru import logger

from src.services.database_service import DatabaseService
from src.services.connectors import ConnectorFactory
from src.services.supabase_client import supabase_client


async def bulk_normalize_products(supplier_id: str, batch_size: int = 1000, max_count: int = None):
    """대량 상품 정규화 처리"""
    
    db = DatabaseService()
    
    logger.info("="*70)
    logger.info("🔄 대량 상품 정규화 시작")
    logger.info(f"   공급사 ID: {supplier_id}")
    logger.info(f"   배치 크기: {batch_size}")
    logger.info(f"   최대 처리: {max_count if max_count else '전체'}")
    logger.info("="*70)
    
    start_time = datetime.now()
    
    # 1단계: 공급사 정보 조회
    logger.info("\n1️⃣ 공급사 정보 조회 중...")
    suppliers = await db.select_data("suppliers", {"id": supplier_id})
    
    if not suppliers:
        logger.error(f"공급사를 찾을 수 없습니다: {supplier_id}")
        return {"status": "error", "message": "Supplier not found"}
    
    supplier = suppliers[0]
    logger.info(f"   공급사: {supplier['name']} ({supplier['code']})")
    
    # 2단계: 계정 정보 조회
    logger.info("\n2️⃣ 계정 정보 조회 중...")
    accounts = await db.select_data("supplier_accounts", {"supplier_id": supplier_id, "is_active": True})
    
    if not accounts:
        logger.error(f"활성 계정이 없습니다: {supplier_id}")
        return {"status": "error", "message": "No active accounts"}
    
    account = accounts[0]
    logger.info(f"   계정: {account['account_name']}")
    
    # 3단계: 커넥터 생성
    logger.info("\n3️⃣ 커넥터 생성 중...")
    
    credentials = json.loads(account['account_credentials']) if isinstance(account['account_credentials'], str) else account['account_credentials']
    
    # api_config 안전하게 처리
    api_config = supplier.get('api_config', {})
    if isinstance(api_config, str):
        api_config = json.loads(api_config)
    if not api_config:
        api_config = {}
    
    from src.services.connectors import CollectionMethod
    
    # supplier type 가져오기
    supplier_type_str = supplier.get('type', 'api')
    supplier_type = CollectionMethod(supplier_type_str)
    
    connector = ConnectorFactory.create(
        supplier_code=supplier['code'],
        supplier_id=UUID(supplier_id),
        supplier_type=supplier_type,
        credentials=credentials,
        config=api_config
    )
    
    logger.info(f"   커넥터: {connector.__class__.__name__}")
    
    # 4단계: 미처리 데이터 조회
    logger.info("\n4️⃣ 미처리 데이터 조회 중...")
    
    offset = 0
    total_raw_count = 0
    
    # 전체 개수 확인
    count_response = (
        supabase_client.get_table("raw_product_data")
        .select("id", count="exact")
        .eq("supplier_id", supplier_id)
        .eq("is_processed", False)
        .execute()
    )
    
    total_raw_count = count_response.count
    logger.info(f"   미처리 데이터: {total_raw_count:,}개")
    
    if max_count:
        total_raw_count = min(total_raw_count, max_count)
        logger.info(f"   처리 제한: {total_raw_count:,}개")
    
    # 5단계: 배치 처리
    logger.info(f"\n5️⃣ 배치 정규화 시작 (배치 크기: {batch_size})...")
    
    success_count = 0
    failed_count = 0
    batch_num = 0
    total_batches = (total_raw_count + batch_size - 1) // batch_size
    
    while offset < total_raw_count:
        batch_num += 1
        
        # 배치 데이터 조회
        logger.info(f"\n   배치 {batch_num}/{total_batches} 조회 중... (offset: {offset})")
        
        raw_data_batch = (
            supabase_client.get_table("raw_product_data")
            .select("*")
            .eq("supplier_id", supplier_id)
            .eq("is_processed", False)
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        
        if not raw_data_batch.data:
            logger.info("   더 이상 처리할 데이터가 없습니다")
            break
        
        batch_items = raw_data_batch.data
        logger.info(f"   배치 {batch_num}: {len(batch_items)}개 정규화 중...")
        
        # 정규화된 상품 리스트
        normalized_batch = []
        processed_ids = []
        
        for idx, raw_item in enumerate(batch_items, 1):
            try:
                # raw_data 파싱
                raw_data = raw_item['raw_data']
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                # 커넥터로 변환
                normalized_data = await connector.transform_product(raw_data)
                
                # 정규화된 상품 데이터
                normalized_product = {
                    "raw_data_id": raw_item['id'],
                    "supplier_id": supplier_id,
                    "supplier_product_id": normalized_data.get('supplier_product_id', ''),
                    "title": normalized_data.get('title', ''),
                    "description": normalized_data.get('description', ''),
                    "price": float(normalized_data.get('price', 0)),
                    "cost_price": float(normalized_data.get('cost_price', 0)),
                    "currency": normalized_data.get('currency', 'KRW'),
                    "category": normalized_data.get('category', ''),
                    "brand": normalized_data.get('brand', ''),
                    "stock_quantity": int(normalized_data.get('stock_quantity', 0)),
                    "status": normalized_data.get('status', 'active'),
                    "images": json.dumps(normalized_data.get('images', []), ensure_ascii=False),
                    "attributes": json.dumps(normalized_data.get('attributes', {}), ensure_ascii=False)
                }
                
                normalized_batch.append(normalized_product)
                processed_ids.append(raw_item['id'])
                
                if idx % 100 == 0:
                    logger.info(f"      진행: {idx}/{len(batch_items)}개")
                
            except Exception as e:
                logger.warning(f"      정규화 실패: {raw_item.get('id')}, {e}")
                failed_count += 1
                continue
        
        # 6단계: 정규화 데이터 bulk insert
        if normalized_batch:
            logger.info(f"   배치 {batch_num}: {len(normalized_batch)}개 저장 중...")
            
            try:
                # bulk insert로 저장
                saved_count = await db.bulk_insert("normalized_products", normalized_batch)
                success_count += saved_count
                logger.info(f"   배치 {batch_num} 저장 완료: {saved_count}개")
                
            except Exception as e:
                logger.error(f"   배치 {batch_num} 저장 실패: {e}")
                # 실패시 bulk upsert로 재시도
                try:
                    saved_count = await db.bulk_upsert("normalized_products", normalized_batch)
                    success_count += saved_count
                    logger.info(f"   배치 {batch_num} upsert 완료: {saved_count}개")
                except Exception as e2:
                    logger.error(f"   upsert도 실패: {e2}")
                    failed_count += len(normalized_batch)
        
        # 7단계: 처리 완료 표시 (작은 배치로)
        if processed_ids:
            logger.info(f"   배치 {batch_num}: {len(processed_ids)}개 처리 완료 표시 중...")
            
            try:
                # 100개씩 나눠서 업데이트 (414 에러 방지)
                update_batch_size = 100
                for i in range(0, len(processed_ids), update_batch_size):
                    id_chunk = processed_ids[i:i + update_batch_size]
                    
                    update_query = (
                        supabase_client.get_table("raw_product_data")
                        .update({"is_processed": True, "processed_at": datetime.now().isoformat()})
                        .in_("id", id_chunk)
                        .execute()
                    )
                
                logger.info(f"   배치 {batch_num} 처리 완료 표시 완료")
                
            except Exception as e:
                logger.error(f"   처리 완료 표시 실패: {e}")
        
        # 진행률 계산
        progress = ((offset + len(batch_items)) / total_raw_count) * 100
        logger.info(f"   배치 {batch_num} 완료: 성공 {len(normalized_batch)}개 (누적: {success_count}/{total_raw_count}, 진행률: {progress:.1f}%)")
        
        offset += batch_size
        
        # API 호출 간격
        await asyncio.sleep(0.1)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ 대량 정규화 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"   처리 데이터: {total_raw_count:,}개")
    logger.info(f"   성공: {success_count:,}개")
    logger.info(f"   실패: {failed_count:,}개")
    logger.info(f"   성공률: {(success_count/total_raw_count*100):.1f}%" if total_raw_count > 0 else "   성공률: N/A")
    logger.info(f"   총 시간: {total_time/60:.2f}분")
    logger.info(f"   처리 속도: {success_count/total_time:.1f}개/초" if total_time > 0 else "   처리 속도: N/A")
    logger.info(f"{'='*70}")
    
    result = {
        "status": "success",
        "total": total_raw_count,
        "success": success_count,
        "failed": failed_count,
        "success_rate": (success_count/total_raw_count*100) if total_raw_count > 0 else 0,
        "total_time": total_time,
        "processing_speed": success_count/total_time if total_time > 0 else 0
    }
    
    with open('bulk_normalization_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info("💾 결과가 bulk_normalization_result.json에 저장되었습니다")
    
    return result


if __name__ == "__main__":
    import sys
    
    # 명령줄 인자로 공급사와 최대 개수 설정 가능
    # 사용법: python process_bulk_normalization.py [supplier_code] [max_count]
    
    supplier_codes = {
        'ownerclan': 'e458e4e2-cb03-4fc2-bff1-b05aaffde00f',
        'zentrade': '959ddf49-c25f-4ebb-a292-bc4e0f1cd28a',
        'domaemae': 'baa2ccd3-a328-4387-b307-6ae89aea331b'
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in supplier_codes:
        supplier_code = sys.argv[1]
        supplier_id = supplier_codes[supplier_code]
        max_count = int(sys.argv[2]) if len(sys.argv) > 2 else None
    else:
        # 기본값: 오너클랜
        supplier_id = supplier_codes['ownerclan']
        max_count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    # 데이터 정규화
    result = asyncio.run(bulk_normalize_products(
        supplier_id=supplier_id,
        batch_size=1000,
        max_count=max_count
    ))

