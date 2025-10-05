"""
API 커넥터 실제 테스트 스크립트
3개 공급사 (오너클랜, 젠트레이드, 도매매) 커넥터 실제 연동 테스트
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from loguru import logger
from typing import Dict, Any, Optional

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.connectors.examples.ownerclan import OwnerClanConnector
from src.services.connectors.examples.zentrade import ZentradeConnector
from src.services.connectors.examples.domaemae import DomaeMaeConnector


class APIConnectorTester:
    """API 커넥터 테스트 클래스"""
    
    def __init__(self):
        """테스터 초기화"""
        self.results = {}
        
    async def test_ownerclan_connector(self) -> Dict[str, Any]:
        """오너클랜 커넥터 테스트"""
        logger.info("🔄 오너클랜 커넥터 테스트 시작...")
        
        try:
            # API 키 확인 (실제 키가 있는 경우에만 테스트)
            api_key = os.getenv('OWNERCLAN_API_KEY')
            api_secret = os.getenv('OWNERCLAN_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("⚠️ 오너클랜 API 키가 설정되지 않음 - 스킵")
                return {"status": "skipped", "reason": "API keys not configured"}
            
            # 커넥터 생성
            connector = OwnerClanConnector(
                api_key=api_key,
                api_secret=api_secret
            )
            
            # 1. 인증 테스트
            logger.info("1️⃣ 인증 테스트...")
            auth_result = await connector.validate_credentials()
            
            if not auth_result:
                logger.error("❌ 오너클랜 인증 실패")
                return {"status": "failed", "step": "authentication"}
            
            logger.info("✅ 오너클랜 인증 성공")
            
            # 2. 상품 수집 테스트 (10개 제한)
            logger.info("2️⃣ 상품 수집 테스트 (10개 제한)...")
            products = await connector.collect_products(limit=10)
            
            if not products:
                logger.warning("⚠️ 오너클랜에서 상품을 찾을 수 없음")
                return {"status": "partial", "step": "collection", "products": 0}
            
            logger.info(f"✅ 오너클랜 상품 수집 성공: {len(products)}개")
            
            # 3. 상품 변환 테스트
            logger.info("3️⃣ 상품 변환 테스트...")
            if products:
                transformed = await connector.transform_product(products[0])
                logger.info(f"✅ 상품 변환 성공: {transformed.get('title', 'Unknown')}")
            
            # 4. 상품 상세 조회 테스트
            logger.info("4️⃣ 상품 상세 조회 테스트...")
            if products:
                product_id = products[0].get('id', '')
                if product_id:
                    detail = await connector.get_product_detail(str(product_id))
                    if detail:
                        logger.info("✅ 상품 상세 조회 성공")
                    else:
                        logger.warning("⚠️ 상품 상세 조회 실패")
            
            return {
                "status": "success",
                "products_collected": len(products),
                "auth_success": auth_result
            }
            
        except Exception as e:
            logger.error(f"❌ 오너클랜 테스트 오류: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_zentrade_connector(self) -> Dict[str, Any]:
        """젠트레이드 커넥터 테스트"""
        logger.info("🔄 젠트레이드 커넥터 테스트 시작...")
        
        try:
            # API 키 확인
            api_key = os.getenv('ZENTRADE_API_KEY')
            api_secret = os.getenv('ZENTRADE_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("⚠️ 젠트레이드 API 키가 설정되지 않음 - 스킵")
                return {"status": "skipped", "reason": "API keys not configured"}
            
            # 커넥터 생성
            connector = ZentradeConnector(
                api_key=api_key,
                api_secret=api_secret
            )
            
            # 1. 인증 테스트
            logger.info("1️⃣ 인증 테스트...")
            auth_result = await connector.validate_credentials()
            
            if not auth_result:
                logger.error("❌ 젠트레이드 인증 실패")
                return {"status": "failed", "step": "authentication"}
            
            logger.info("✅ 젠트레이드 인증 성공")
            
            # 2. 상품 수집 테스트 (10개 제한)
            logger.info("2️⃣ 상품 수집 테스트 (10개 제한)...")
            products = await connector.collect_products(limit=10)
            
            if not products:
                logger.warning("⚠️ 젠트레이드에서 상품을 찾을 수 없음")
                return {"status": "partial", "step": "collection", "products": 0}
            
            logger.info(f"✅ 젠트레이드 상품 수집 성공: {len(products)}개")
            
            # 3. 상품 변환 테스트
            logger.info("3️⃣ 상품 변환 테스트...")
            if products:
                transformed = await connector.transform_product(products[0])
                logger.info(f"✅ 상품 변환 성공: {transformed.get('title', 'Unknown')}")
            
            # 4. 카테고리 조회 테스트
            logger.info("4️⃣ 카테고리 조회 테스트...")
            categories = await connector.get_categories()
            if categories:
                logger.info(f"✅ 카테고리 조회 성공: {len(categories)}개")
            else:
                logger.warning("⚠️ 카테고리 조회 실패")
            
            return {
                "status": "success",
                "products_collected": len(products),
                "categories_count": len(categories) if categories else 0,
                "auth_success": auth_result
            }
            
        except Exception as e:
            logger.error(f"❌ 젠트레이드 테스트 오류: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_domaemae_connector(self) -> Dict[str, Any]:
        """도매매 커넥터 테스트"""
        logger.info("🔄 도매매 커넥터 테스트 시작...")
        
        try:
            # API 키 확인
            api_key = os.getenv('DOMAEMAE_API_KEY')
            seller_id = os.getenv('DOMAEMAE_SELLER_ID')
            
            if not api_key or not seller_id:
                logger.warning("⚠️ 도매매 API 키가 설정되지 않음 - 스킵")
                return {"status": "skipped", "reason": "API keys not configured"}
            
            # 커넥터 생성
            connector = DomaeMaeConnector(
                api_key=api_key,
                seller_id=seller_id
            )
            
            # 1. 인증 테스트
            logger.info("1️⃣ 인증 테스트...")
            auth_result = await connector.validate_credentials()
            
            if not auth_result:
                logger.error("❌ 도매매 인증 실패")
                return {"status": "failed", "step": "authentication"}
            
            logger.info("✅ 도매매 인증 성공")
            
            # 2. 상품 수집 테스트 (10개 제한)
            logger.info("2️⃣ 상품 수집 테스트 (10개 제한)...")
            products = await connector.collect_products(limit=10)
            
            if not products:
                logger.warning("⚠️ 도매매에서 상품을 찾을 수 없음")
                return {"status": "partial", "step": "collection", "products": 0}
            
            logger.info(f"✅ 도매매 상품 수집 성공: {len(products)}개")
            
            # 3. 상품 변환 테스트
            logger.info("3️⃣ 상품 변환 테스트...")
            if products:
                transformed = await connector.transform_product(products[0])
                logger.info(f"✅ 상품 변환 성공: {transformed.get('title', 'Unknown')}")
            
            # 4. 재고 확인 테스트
            logger.info("4️⃣ 재고 확인 테스트...")
            if products:
                product_id = products[0].get('goods_no', '')
                if product_id:
                    stock = await connector.check_stock(str(product_id))
                    logger.info(f"✅ 재고 확인 성공: {stock}개")
            
            return {
                "status": "success",
                "products_collected": len(products),
                "auth_success": auth_result
            }
            
        except Exception as e:
            logger.error(f"❌ 도매매 테스트 오류: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 커넥터 테스트 실행"""
        logger.info("🚀 API 커넥터 전체 테스트 시작...")
        
        # 각 커넥터 테스트 실행
        ownerclan_result = await self.test_ownerclan_connector()
        zentrade_result = await self.test_zentrade_connector()
        domaemae_result = await self.test_domaemae_connector()
        
        # 결과 정리
        results = {
            "ownerclan": ownerclan_result,
            "zentrade": zentrade_result,
            "domaemae": domaemae_result,
            "summary": {
                "total_tests": 3,
                "successful": sum(1 for r in [ownerclan_result, zentrade_result, domaemae_result] 
                                if r.get("status") == "success"),
                "skipped": sum(1 for r in [ownerclan_result, zentrade_result, domaemae_result] 
                              if r.get("status") == "skipped"),
                "failed": sum(1 for r in [ownerclan_result, zentrade_result, domaemae_result] 
                             if r.get("status") in ["failed", "error"])
            }
        }
        
        # 결과 출력
        logger.info("📊 테스트 결과 요약:")
        logger.info(f"  총 테스트: {results['summary']['total_tests']}")
        logger.info(f"  성공: {results['summary']['successful']}")
        logger.info(f"  스킵: {results['summary']['skipped']}")
        logger.info(f"  실패: {results['summary']['failed']}")
        
        return results


async def main():
    """메인 함수"""
    logger.info("🔧 API 커넥터 테스트 시작")
    
    # 테스터 생성 및 실행
    tester = APIConnectorTester()
    results = await tester.run_all_tests()
    
    # 결과 저장
    import json
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("✅ 테스트 완료 - 결과가 api_test_results.json에 저장됨")
    
    return results


if __name__ == "__main__":
    # 비동기 메인 함수 실행
    results = asyncio.run(main())
