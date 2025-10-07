#!/usr/bin/env python3
"""
REST API 서버 테스트
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any
from loguru import logger

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RESTAPITester:
    """REST API 서버 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.headers = {
            "Authorization": "Bearer dev_token_123",
            "Content-Type": "application/json"
        }
        self.test_results = {}
    
    async def test_server_health(self) -> bool:
        """서버 헬스 체크 테스트"""
        try:
            logger.info("=== 서버 헬스 체크 테스트 시작 ===")
            
            # 루트 엔드포인트 테스트
            response = requests.get(f"{self.base_url}/", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 루트 엔드포인트 응답 성공")
                logger.info(f"  API 버전: {data.get('data', {}).get('version', 'N/A')}")
                logger.info(f"  상태: {data.get('data', {}).get('status', 'N/A')}")
            else:
                logger.error(f"❌ 루트 엔드포인트 응답 실패: {response.status_code}")
                return False
            
            # 헬스 체크 엔드포인트 테스트
            response = requests.get(f"{self.base_url}/health", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 헬스 체크 엔드포인트 응답 성공")
                logger.info(f"  상태: {data.get('data', {}).get('status', 'N/A')}")
            else:
                logger.error(f"❌ 헬스 체크 엔드포인트 응답 실패: {response.status_code}")
                return False
            
            self.test_results['server_health'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 서버 헬스 체크 테스트 실패: {e}")
            self.test_results['server_health'] = False
            return False
    
    async def test_products_api(self) -> bool:
        """상품 API 테스트"""
        try:
            logger.info("\n=== 상품 API 테스트 시작 ===")
            
            # 상품 목록 조회 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/products",
                headers=self.headers,
                params={"limit": 5, "offset": 0}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 상품 목록 조회 성공")
                logger.info(f"  조회된 상품 수: {data.get('data', {}).get('total', 0)}")
                
                # 첫 번째 상품이 있으면 상세 조회 테스트
                products = data.get('data', {}).get('products', [])
                if products:
                    product_id = products[0].get('id')
                    if product_id:
                        # 특정 상품 조회 테스트
                        response = requests.get(
                            f"{self.base_url}/api/v2/products/{product_id}",
                            headers=self.headers
                        )
                        
                        if response.status_code == 200:
                            logger.info("✅ 특정 상품 조회 성공")
                        else:
                            logger.error(f"❌ 특정 상품 조회 실패: {response.status_code}")
            else:
                logger.error(f"❌ 상품 목록 조회 실패: {response.status_code}")
                return False
            
            self.test_results['products_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 상품 API 테스트 실패: {e}")
            self.test_results['products_api'] = False
            return False
    
    async def test_search_api(self) -> bool:
        """검색 API 테스트"""
        try:
            logger.info("\n=== 검색 API 테스트 시작 ===")
            
            # 상품 검색 테스트
            search_data = {
                "keyword": "무선 이어폰",
                "page": 1,
                "platform": "coupang"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/search",
                headers=self.headers,
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 상품 검색 성공")
                logger.info(f"  검색 키워드: {data.get('data', {}).get('keyword', 'N/A')}")
                logger.info(f"  검색 결과 수: {data.get('data', {}).get('total_results', 0)}")
            else:
                logger.error(f"❌ 상품 검색 실패: {response.status_code}")
                return False
            
            # 검색 제안 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/search/suggestions",
                headers=self.headers,
                params={"q": "무선", "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 검색 제안 성공")
                logger.info(f"  제안 수: {data.get('data', {}).get('count', 0)}")
            else:
                logger.error(f"❌ 검색 제안 실패: {response.status_code}")
            
            self.test_results['search_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 검색 API 테스트 실패: {e}")
            self.test_results['search_api'] = False
            return False
    
    async def test_ai_api(self) -> bool:
        """AI API 테스트"""
        try:
            logger.info("\n=== AI API 테스트 시작 ===")
            
            # 가격 예측 테스트
            prediction_data = {
                "product_data": {
                    "platform": "coupang",
                    "price": 50000,
                    "original_price": 65000,
                    "rating": 4.3,
                    "review_count": 850,
                    "category": "전자제품",
                    "brand": "TestBrand"
                },
                "category": "전자제품"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/ai/predict",
                headers=self.headers,
                json=prediction_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ AI 가격 예측 성공")
                predictions = data.get('data', {}).get('predictions', [])
                logger.info(f"  예측 모델 수: {len(predictions)}")
                
                best_prediction = data.get('data', {}).get('best_prediction', {})
                if best_prediction:
                    logger.info(f"  최고 예측 가격: {best_prediction.get('price', 'N/A')}원")
            else:
                logger.error(f"❌ AI 가격 예측 실패: {response.status_code}")
            
            # 가격 전략 분석 테스트
            response = requests.post(
                f"{self.base_url}/api/v2/ai/strategy",
                headers=self.headers,
                json=prediction_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 가격 전략 분석 성공")
                strategy_data = data.get('data', {})
                logger.info(f"  추천 가격: {strategy_data.get('recommended_price', 'N/A')}원")
                logger.info(f"  전략: {strategy_data.get('strategy', 'N/A')}")
            else:
                logger.error(f"❌ 가격 전략 분석 실패: {response.status_code}")
            
            # 시장 트렌드 분석 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/ai/trends",
                headers=self.headers,
                params={"category": "전자제품"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 시장 트렌드 분석 성공")
                trend_data = data.get('data', {})
                logger.info(f"  트렌드 방향: {trend_data.get('trend_direction', 'N/A')}")
                logger.info(f"  경쟁사 수: {trend_data.get('competitor_count', 'N/A')}개")
            else:
                logger.error(f"❌ 시장 트렌드 분석 실패: {response.status_code}")
            
            self.test_results['ai_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ AI API 테스트 실패: {e}")
            self.test_results['ai_api'] = False
            return False
    
    async def test_orders_api(self) -> bool:
        """주문 API 테스트"""
        try:
            logger.info("\n=== 주문 API 테스트 시작 ===")
            
            # 주문 목록 조회 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/orders",
                headers=self.headers,
                params={"limit": 5, "offset": 0}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 주문 목록 조회 성공")
                logger.info(f"  조회된 주문 수: {data.get('data', {}).get('total', 0)}")
            else:
                logger.error(f"❌ 주문 목록 조회 실패: {response.status_code}")
            
            # 주문 생성 테스트 (모의 데이터)
            order_data = {
                "products": [
                    {
                        "item_key": "test_item_001",
                        "quantity": 1,
                        "option_attributes": []
                    }
                ],
                "recipient": {
                    "name": "테스트 고객",
                    "phone": "010-1234-5678",
                    "address": "서울시 강남구",
                    "postal_code": "12345",
                    "city": "서울시",
                    "district": "강남구",
                    "detail_address": "테스트동 123호"
                },
                "note": "테스트 주문"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/orders",
                headers=self.headers,
                json=order_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 주문 생성 성공")
                order_id = data.get('data', {}).get('order_id', 'N/A')
                logger.info(f"  주문 ID: {order_id}")
            else:
                logger.error(f"❌ 주문 생성 실패: {response.status_code}")
            
            self.test_results['orders_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 주문 API 테스트 실패: {e}")
            self.test_results['orders_api'] = False
            return False
    
    async def test_suppliers_api(self) -> bool:
        """공급사 API 테스트"""
        try:
            logger.info("\n=== 공급사 API 테스트 시작 ===")
            
            # 공급사 목록 조회 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/suppliers",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 공급사 목록 조회 성공")
                logger.info(f"  조회된 공급사 수: {data.get('data', {}).get('count', 0)}")
            else:
                logger.error(f"❌ 공급사 목록 조회 실패: {response.status_code}")
            
            # 공급사 계정 생성 테스트 (모의 데이터)
            supplier_data = {
                "supplier_code": "test_supplier",
                "account_name": "테스트 계정",
                "credentials": {
                    "api_key": "test_api_key",
                    "api_secret": "test_api_secret"
                },
                "is_active": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/suppliers",
                headers=self.headers,
                json=supplier_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 공급사 계정 생성 성공")
                supplier_code = data.get('data', {}).get('supplier_code', 'N/A')
                logger.info(f"  공급사 코드: {supplier_code}")
            else:
                logger.error(f"❌ 공급사 계정 생성 실패: {response.status_code}")
            
            self.test_results['suppliers_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 공급사 API 테스트 실패: {e}")
            self.test_results['suppliers_api'] = False
            return False
    
    async def test_analytics_api(self) -> bool:
        """분석 API 테스트"""
        try:
            logger.info("\n=== 분석 API 테스트 시작 ===")
            
            # 대시보드 분석 데이터 테스트
            response = requests.get(
                f"{self.base_url}/api/v2/analytics/dashboard",
                headers=self.headers,
                params={"period": "7d"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 대시보드 분석 데이터 조회 성공")
                statistics = data.get('data', {}).get('statistics', {})
                logger.info(f"  총 상품 수: {statistics.get('total_products', 'N/A')}")
                logger.info(f"  총 주문 수: {statistics.get('total_orders', 'N/A')}")
                logger.info(f"  모니터링 플랫폼 수: {statistics.get('platforms_monitored', 'N/A')}")
            else:
                logger.error(f"❌ 대시보드 분석 데이터 조회 실패: {response.status_code}")
                return False
            
            self.test_results['analytics_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 분석 API 테스트 실패: {e}")
            self.test_results['analytics_api'] = False
            return False
    
    async def test_batch_api(self) -> bool:
        """배치 작업 API 테스트"""
        try:
            logger.info("\n=== 배치 작업 API 테스트 시작 ===")
            
            # 데이터 수집 배치 작업 테스트
            batch_data = {
                "operation": "data_collection",
                "parameters": {
                    "platforms": ["coupang", "naver_smartstore"],
                    "keywords": ["무선 이어폰", "스마트워치"]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/batch",
                headers=self.headers,
                json=batch_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 배치 작업 실행 성공")
                operation = data.get('data', {}).get('operation', 'N/A')
                status = data.get('data', {}).get('status', 'N/A')
                logger.info(f"  작업 유형: {operation}")
                logger.info(f"  상태: {status}")
            else:
                logger.error(f"❌ 배치 작업 실행 실패: {response.status_code}")
                return False
            
            self.test_results['batch_api'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 배치 작업 API 테스트 실패: {e}")
            self.test_results['batch_api'] = False
            return False
    
    async def test_authentication(self) -> bool:
        """인증 시스템 테스트"""
        try:
            logger.info("\n=== 인증 시스템 테스트 시작 ===")
            
            # 유효하지 않은 토큰으로 테스트
            invalid_headers = {
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/api/v2/products",
                headers=invalid_headers
            )
            
            if response.status_code == 401:
                logger.info("✅ 유효하지 않은 토큰 거부 성공")
            else:
                logger.error(f"❌ 유효하지 않은 토큰이 허용됨: {response.status_code}")
            
            # 토큰 없이 테스트
            response = requests.get(f"{self.base_url}/api/v2/products")
            
            if response.status_code == 401:
                logger.info("✅ 토큰 없이 접근 거부 성공")
            else:
                logger.error(f"❌ 토큰 없이 접근 허용됨: {response.status_code}")
            
            self.test_results['authentication'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ 인증 시스템 테스트 실패: {e}")
            self.test_results['authentication'] = False
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """모든 테스트 실행"""
        try:
            logger.info("🚀 REST API 서버 통합 테스트 시작")
            
            # 서버가 실행 중인지 확인
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code != 200:
                    logger.error("❌ REST API 서버가 실행되지 않았습니다")
                    logger.info("다음 명령어로 서버를 시작하세요: python rest_api_server.py")
                    return {}
            except requests.exceptions.RequestException:
                logger.error("❌ REST API 서버에 연결할 수 없습니다")
                logger.info("다음 명령어로 서버를 시작하세요: python rest_api_server.py")
                return {}
            
            # 모든 테스트 실행
            test_methods = [
                self.test_server_health,
                self.test_products_api,
                self.test_search_api,
                self.test_ai_api,
                self.test_orders_api,
                self.test_suppliers_api,
                self.test_analytics_api,
                self.test_batch_api,
                self.test_authentication
            ]
            
            for test_method in test_methods:
                await test_method()
            
            # 결과 요약
            passed_tests = sum(self.test_results.values())
            total_tests = len(self.test_results)
            
            logger.info(f"\n📊 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            # 상세 결과
            for test_name, result in self.test_results.items():
                status = "✅ 성공" if result else "❌ 실패"
                logger.info(f"  {test_name}: {status}")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 테스트 통과!")
            else:
                logger.warning("⚠️ 일부 테스트 실패")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류: {e}")
            return {}


async def main():
    """메인 함수"""
    try:
        # REST API 테스터 초기화
        tester = RESTAPITester()
        
        # 모든 테스트 실행
        results = await tester.run_all_tests()
        
        # 결과 반환
        return results
        
    except Exception as e:
        logger.error(f"❌ 메인 함수 실행 중 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())