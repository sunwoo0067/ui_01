"""
데이터베이스 중심 아키텍처 개선안
공급사 API 계정 정보를 DB에서 관리하고 데이터 수집을 우선시하는 시스템
"""

import asyncio
import sys
import os
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import json

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.supabase_client import supabase_client
from src.services.connectors.factory import ConnectorFactory
from src.services.collection_service import CollectionService
from src.services.product_pipeline import ProductPipeline
from src.utils.error_handler import ErrorHandler


class DatabaseCentricArchitecture:
    """데이터베이스 중심 아키텍처 클래스"""
    
    def __init__(self):
        self.supabase = supabase_client
        self.connector_factory = ConnectorFactory()
        self.collection_service = CollectionService()
        self.product_pipeline = ProductPipeline()
    
    async def setup_supplier_accounts(self) -> Dict[str, Any]:
        """공급사 계정 정보를 DB에서 설정"""
        print("🔄 공급사 계정 정보 DB 설정...")
        
        # 1. 공급사 기본 정보 등록
        suppliers_data = [
            {
                "name": "오너클랜",
                "code": "ownerclan",
                "type": "api",
                "api_endpoint": "https://api.ownerclan.com/v1",
                "api_version": "v1",
                "auth_type": "api_key",
                "field_mapping": {
                    "product_id": "supplier_product_id",
                    "title": "title",
                    "price": "price",
                    "category": "category",
                    "stock": "stock_quantity",
                    "description": "description",
                    "images": "images"
                },
                "is_active": True
            },
            {
                "name": "젠트레이드",
                "code": "zentrade", 
                "type": "api",
                "api_endpoint": "https://api.zentrade.com/api/v1",
                "api_version": "v1",
                "auth_type": "api_key",
                "field_mapping": {
                    "product_id": "supplier_product_id",
                    "title": "title",
                    "price": "price",
                    "category": "category",
                    "stock": "stock_quantity",
                    "description": "description",
                    "images": "images"
                },
                "is_active": True
            },
            {
                "name": "도매매",
                "code": "domaemae",
                "type": "api", 
                "api_endpoint": "https://api.dodomall.com/v2",
                "api_version": "v2",
                "auth_type": "api_key",
                "field_mapping": {
                    "product_id": "supplier_product_id",
                    "title": "title",
                    "price": "price",
                    "category": "category",
                    "stock": "stock_quantity",
                    "description": "description",
                    "images": "images"
                },
                "is_active": True
            }
        ]
        
        # 공급사 등록
        supplier_ids = {}
        for supplier_data in suppliers_data:
            try:
                result = self.supabase.get_table('suppliers').insert(supplier_data).execute()
                if result.data:
                    supplier_id = result.data[0]['id']
                    supplier_ids[supplier_data['code']] = supplier_id
                    print(f"✅ {supplier_data['name']} 공급사 등록 완료: {supplier_id}")
            except Exception as e:
                print(f"⚠️ {supplier_data['name']} 공급사 등록 실패: {e}")
        
        # 2. 공급사 계정 정보 등록 (실제 API 키 사용)
        supplier_accounts_data = [
            {
                "supplier_id": supplier_ids.get("ownerclan"),
                "account_name": "오너클랜 메인 계정",
                "account_credentials": {
                    "api_key": "YOUR_OWNERCLAN_API_KEY",  # 실제 API 키로 교체
                    "api_secret": "YOUR_OWNERCLAN_API_SECRET"  # 실제 시크릿으로 교체
                },
                "is_active": True,
                "priority": 1
            },
            {
                "supplier_id": supplier_ids.get("zentrade"),
                "account_name": "젠트레이드 메인 계정", 
                "account_credentials": {
                    "api_key": "YOUR_ZENTRADE_API_KEY",  # 실제 API 키로 교체
                    "api_secret": "YOUR_ZENTRADE_API_SECRET"  # 실제 시크릿으로 교체
                },
                "is_active": True,
                "priority": 1
            },
            {
                "supplier_id": supplier_ids.get("domaemae"),
                "account_name": "도매매 메인 계정",
                "account_credentials": {
                    "api_key": "YOUR_DOMAEMAE_API_KEY",  # 실제 API 키로 교체
                    "api_secret": "YOUR_DOMAEMAE_API_SECRET",  # 실제 시크릿으로 교체
                    "seller_id": "YOUR_SELLER_ID"  # 도매매 전용
                },
                "is_active": True,
                "priority": 1
            }
        ]
        
        # 공급사 계정 등록
        account_ids = {}
        for account_data in supplier_accounts_data:
            if account_data['supplier_id']:  # 공급사가 등록된 경우만
                try:
                    result = self.supabase.get_table('supplier_accounts').insert(account_data).execute()
                    if result.data:
                        account_id = result.data[0]['id']
                        account_ids[account_data['account_name']] = account_id
                        print(f"✅ {account_data['account_name']} 계정 등록 완료: {account_id}")
                except Exception as e:
                    print(f"⚠️ {account_data['account_name']} 계정 등록 실패: {e}")
        
        return {
            "supplier_ids": supplier_ids,
            "account_ids": account_ids
        }
    
    async def collect_supplier_data(self, supplier_code: str, limit: int = 100) -> Dict[str, Any]:
        """공급사 데이터 수집 (DB 계정 정보 사용)"""
        print(f"🔄 {supplier_code} 공급사 데이터 수집 시작...")
        
        try:
            # 1. DB에서 공급사 및 계정 정보 조회
            supplier_result = self.supabase.get_table('suppliers').select('*').eq('code', supplier_code).execute()
            if not supplier_result.data:
                raise ValueError(f"공급사를 찾을 수 없습니다: {supplier_code}")
            
            supplier = supplier_result.data[0]
            supplier_id = supplier['id']
            
            # 활성화된 계정 조회
            accounts_result = self.supabase.get_table('supplier_accounts').select('*').eq('supplier_id', supplier_id).eq('is_active', True).execute()
            if not accounts_result.data:
                raise ValueError(f"활성화된 계정을 찾을 수 없습니다: {supplier_code}")
            
            account = accounts_result.data[0]
            account_id = account['id']
            
            print(f"   공급사: {supplier['name']}")
            print(f"   계정: {account['account_name']}")
            
            # 2. 커넥터 생성 (DB 정보 사용)
            connector = self.connector_factory.get_connector(
                supplier_type=supplier['type'],
                supplier_id=supplier_id,
                credentials=account['account_credentials'],
                api_config={
                    'base_url': supplier['api_endpoint'],
                    'timeout': 30
                }
            )
            
            # 3. 데이터 수집 실행
            collection_job = await self.collection_service.collect_from_supplier(
                supplier_id=supplier_id,
                supplier_account_id=account_id,
                limit=limit
            )
            
            print(f"✅ {supplier_code} 데이터 수집 완료: {collection_job}")
            
            return {
                "supplier_id": supplier_id,
                "account_id": account_id,
                "collection_job": collection_job,
                "status": "success"
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": f"collect_supplier_data_{supplier_code}"})
            return {
                "supplier_code": supplier_code,
                "status": "error",
                "message": str(e)
            }
    
    async def process_collected_data(self, supplier_id: str) -> Dict[str, Any]:
        """수집된 데이터 처리 및 정규화"""
        print(f"🔄 {supplier_id} 수집 데이터 처리 시작...")
        
        try:
            # 1. 수집된 원본 데이터 확인
            raw_data_result = self.supabase.get_table('raw_product_data').select('*').eq('supplier_id', supplier_id).execute()
            raw_count = len(raw_data_result.data)
            print(f"   원본 데이터: {raw_count}개")
            
            if raw_count == 0:
                return {"status": "no_data", "message": "처리할 원본 데이터가 없습니다"}
            
            # 2. 데이터 변환 및 정규화
            processed_count = await self.product_pipeline.process_all_unprocessed(supplier_id)
            print(f"   처리된 데이터: {processed_count}개")
            
            # 3. 처리 결과 확인
            normalized_result = self.supabase.get_table('normalized_products').select('*').eq('supplier_id', supplier_id).execute()
            normalized_count = len(normalized_result.data)
            print(f"   정규화된 데이터: {normalized_count}개")
            
            return {
                "supplier_id": supplier_id,
                "raw_count": raw_count,
                "processed_count": processed_count,
                "normalized_count": normalized_count,
                "status": "success"
            }
            
        except Exception as e:
            ErrorHandler.log_error(e, {"operation": f"process_collected_data_{supplier_id}"})
            return {
                "supplier_id": supplier_id,
                "status": "error",
                "message": str(e)
            }
    
    async def build_database_ecosystem(self) -> Dict[str, Any]:
        """데이터베이스 생태계 구축"""
        print("🚀 데이터베이스 중심 생태계 구축 시작...")
        
        # 1. 공급사 계정 설정
        setup_result = await self.setup_supplier_accounts()
        
        # 2. 각 공급사별 데이터 수집
        collection_results = {}
        for supplier_code in ["ownerclan", "zentrade", "domaemae"]:
            if supplier_code in setup_result["supplier_ids"]:
                collection_result = await self.collect_supplier_data(supplier_code, limit=50)
                collection_results[supplier_code] = collection_result
                
                # 3. 수집된 데이터 처리
                if collection_result.get("status") == "success":
                    supplier_id = collection_result["supplier_id"]
                    process_result = await self.process_collected_data(supplier_id)
                    collection_results[supplier_code]["processing"] = process_result
        
        # 4. 전체 통계
        total_raw = sum(result.get("processing", {}).get("raw_count", 0) for result in collection_results.values())
        total_normalized = sum(result.get("processing", {}).get("normalized_count", 0) for result in collection_results.values())
        
        print(f"\n📊 데이터베이스 생태계 구축 완료:")
        print(f"   - 총 원본 데이터: {total_raw}개")
        print(f"   - 총 정규화 데이터: {total_normalized}개")
        print(f"   - 활성 공급사: {len(setup_result['supplier_ids'])}개")
        print(f"   - 활성 계정: {len(setup_result['account_ids'])}개")
        
        return {
            "setup_result": setup_result,
            "collection_results": collection_results,
            "total_raw": total_raw,
            "total_normalized": total_normalized,
            "status": "success"
        }


class TransactionSystemDesign:
    """트랜잭션 시스템 설계"""
    
    def __init__(self):
        self.supabase = supabase_client
    
    async def design_transaction_system(self) -> Dict[str, Any]:
        """트랜잭션 시스템 설계안"""
        print("🔄 트랜잭션 시스템 설계...")
        
        # 트랜잭션 시스템 설계안
        transaction_design = {
            "concept": "데이터베이스 중심 트랜잭션 시스템",
            "phases": [
                {
                    "phase": 1,
                    "name": "데이터 수집 및 구축",
                    "description": "공급사에서 데이터를 수집하여 데이터베이스 구축",
                    "priority": "최우선",
                    "components": [
                        "공급사 API 연동",
                        "원본 데이터 저장 (raw_product_data)",
                        "데이터 정규화 (normalized_products)",
                        "이미지 처리 및 저장"
                    ]
                },
                {
                    "phase": 2,
                    "name": "마켓플레이스 데이터 수집",
                    "description": "마켓플레이스에서 경쟁사 데이터 수집",
                    "priority": "높음",
                    "components": [
                        "마켓플레이스 API 연동",
                        "경쟁사 상품 데이터 수집",
                        "가격 모니터링 시스템",
                        "트렌드 분석"
                    ]
                },
                {
                    "phase": 3,
                    "name": "트랜잭션 시스템 구현",
                    "description": "실제 판매 트랜잭션 처리 시스템",
                    "priority": "중간",
                    "components": [
                        "주문 처리 시스템",
                        "재고 관리",
                        "결제 처리",
                        "배송 관리",
                        "고객 관리"
                    ]
                },
                {
                    "phase": 4,
                    "name": "자동화 및 최적화",
                    "description": "전체 시스템 자동화 및 성능 최적화",
                    "priority": "낮음",
                    "components": [
                        "자동 가격 조정",
                        "자동 재고 관리",
                        "성능 모니터링",
                        "머신러닝 기반 추천"
                    ]
                }
            ],
            "database_tables": [
                "suppliers (공급사)",
                "supplier_accounts (공급사 계정)",
                "raw_product_data (원본 상품 데이터)",
                "normalized_products (정규화된 상품)",
                "marketplaces (마켓플레이스)",
                "marketplace_accounts (마켓플레이스 계정)",
                "competitor_products (경쟁사 상품)",
                "price_history (가격 이력)",
                "orders (주문)",
                "transactions (거래)",
                "inventory (재고)",
                "customers (고객)"
            ],
            "api_endpoints": [
                "GET /api/suppliers - 공급사 목록",
                "POST /api/suppliers/{id}/collect - 데이터 수집",
                "GET /api/products - 상품 목록",
                "GET /api/products/{id} - 상품 상세",
                "POST /api/products/{id}/list - 상품 등록",
                "GET /api/competitors - 경쟁사 분석",
                "POST /api/orders - 주문 생성",
                "GET /api/transactions - 거래 내역"
            ]
        }
        
        print("✅ 트랜잭션 시스템 설계 완료")
        
        return transaction_design
    
    async def create_transaction_tables(self) -> Dict[str, Any]:
        """트랜잭션 관련 테이블 생성"""
        print("🔄 트랜잭션 테이블 생성...")
        
        # 트랜잭션 관련 테이블 SQL
        transaction_tables_sql = """
        -- 주문 테이블
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            order_number TEXT UNIQUE NOT NULL,
            customer_id UUID,
            marketplace_id UUID REFERENCES marketplaces(id),
            marketplace_order_id TEXT,
            
            -- 주문 정보
            order_status TEXT DEFAULT 'pending' CHECK (order_status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
            order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            total_amount DECIMAL(10,2) NOT NULL,
            currency TEXT DEFAULT 'KRW',
            
            -- 배송 정보
            shipping_address JSONB,
            shipping_method TEXT,
            tracking_number TEXT,
            
            -- 메타데이터
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 주문 상품 테이블
        CREATE TABLE IF NOT EXISTS order_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
            product_id UUID REFERENCES normalized_products(id),
            supplier_id UUID REFERENCES suppliers(id),
            
            -- 상품 정보
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            
            -- 상태
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 거래 테이블
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            order_id UUID REFERENCES orders(id),
            transaction_type TEXT NOT NULL CHECK (transaction_type IN ('sale', 'refund', 'commission', 'fee')),
            
            -- 금액 정보
            amount DECIMAL(10,2) NOT NULL,
            currency TEXT DEFAULT 'KRW',
            commission_rate DECIMAL(5,2),
            net_amount DECIMAL(10,2),
            
            -- 상태
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
            processed_at TIMESTAMP WITH TIME ZONE,
            
            -- 메타데이터
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 재고 테이블
        CREATE TABLE IF NOT EXISTS inventory (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            product_id UUID REFERENCES normalized_products(id),
            supplier_id UUID REFERENCES suppliers(id),
            
            -- 재고 정보
            available_quantity INTEGER DEFAULT 0,
            reserved_quantity INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 0,
            max_stock_level INTEGER,
            
            -- 상태
            is_active BOOLEAN DEFAULT true,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            UNIQUE(product_id, supplier_id)
        );
        
        -- 고객 테이블
        CREATE TABLE IF NOT EXISTS customers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            marketplace_id UUID REFERENCES marketplaces(id),
            marketplace_customer_id TEXT,
            
            -- 고객 정보
            name TEXT,
            email TEXT,
            phone TEXT,
            
            -- 주소 정보
            addresses JSONB,
            
            -- 통계
            total_orders INTEGER DEFAULT 0,
            total_spent DECIMAL(10,2) DEFAULT 0,
            
            -- 메타데이터
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            UNIQUE(marketplace_id, marketplace_customer_id)
        );
        """
        
        try:
            # SQL 실행
            result = self.supabase.get_client().rpc('exec_sql', {'sql': transaction_tables_sql}).execute()
            print("✅ 트랜잭션 테이블 생성 완료")
            
            return {
                "status": "success",
                "tables_created": [
                    "orders",
                    "order_items", 
                    "transactions",
                    "inventory",
                    "customers"
                ]
            }
            
        except Exception as e:
            print(f"⚠️ 트랜잭션 테이블 생성 실패: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


async def main():
    """메인 함수"""
    print("🚀 데이터베이스 중심 아키텍처 개선 시작...")
    
    # 1. 데이터베이스 중심 아키텍처 구축
    db_arch = DatabaseCentricArchitecture()
    ecosystem_result = await db_arch.build_database_ecosystem()
    
    # 2. 트랜잭션 시스템 설계
    transaction_designer = TransactionSystemDesign()
    design_result = await transaction_designer.design_transaction_system()
    
    # 3. 트랜잭션 테이블 생성
    table_result = await transaction_designer.create_transaction_tables()
    
    # 결과 종합
    final_result = {
        "database_ecosystem": ecosystem_result,
        "transaction_design": design_result,
        "transaction_tables": table_result,
        "recommendations": [
            "1. 공급사 API 키를 실제 값으로 교체하여 데이터 수집 테스트",
            "2. 수집된 데이터의 품질 검증 및 정규화 프로세스 개선",
            "3. 마켓플레이스 경쟁사 데이터 수집 시스템 구축",
            "4. 트랜잭션 시스템 단계별 구현 (주문 → 결제 → 배송)",
            "5. 실시간 재고 관리 및 가격 모니터링 시스템 구축"
        ]
    }
    
    # 결과 저장
    with open("database_centric_architecture_results.json", "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 데이터베이스 중심 아키텍처 개선 완료!")
    print("   결과가 database_centric_architecture_results.json에 저장됨")
    
    return final_result


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(main())
