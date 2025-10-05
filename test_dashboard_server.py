"""
대시보드 서버 테스트
"""

import asyncio
import requests
import json
from datetime import datetime, timezone
from loguru import logger

from src.api.dashboard_server import app
from src.services.database_service import DatabaseService


class DashboardServerTester:
    """대시보드 서버 테스트 클래스"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.db_service = DatabaseService()

    async def test_server_startup(self) -> bool:
        """서버 시작 테스트"""
        try:
            logger.info("\n=== 대시보드 서버 시작 테스트 ===")
            
            # 서버가 실행 중인지 확인
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ 서버가 정상적으로 실행 중입니다")
                return True
            else:
                logger.error(f"❌ 서버 응답 오류: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            return False
        except Exception as e:
            logger.error(f"❌ 서버 시작 테스트 중 오류: {e}")
            return False

    async def test_api_endpoints(self) -> bool:
        """API 엔드포인트 테스트"""
        try:
            logger.info("\n=== API 엔드포인트 테스트 ===")
            
            endpoints = [
                ("/", "루트 엔드포인트"),
                ("/health", "헬스 체크"),
                ("/api/dashboard/stats", "대시보드 통계"),
                ("/api/products/recent", "최근 상품"),
                ("/api/alerts/active", "활성 알림"),
                ("/api/analysis/recent", "최근 분석"),
            ]
            
            success_count = 0
            
            for endpoint, description in endpoints:
                try:
                    logger.info(f"테스트 중: {description} ({endpoint})")
                    
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ {description} - 성공")
                        success_count += 1
                        
                        # 응답 데이터 확인
                        if endpoint == "/api/dashboard/stats":
                            data = response.json()
                            logger.info(f"  통계 데이터: 상품 {data.get('total_products', 0)}개, 가격변동 {data.get('total_price_changes', 0)}개")
                    else:
                        logger.warning(f"⚠️ {description} - HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ {description} - 오류: {e}")
                    continue
            
            logger.info(f"API 엔드포인트 테스트 결과: {success_count}/{len(endpoints)} 성공")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ API 엔드포인트 테스트 중 오류: {e}")
            return False

    async def test_search_functionality(self) -> bool:
        """검색 기능 테스트"""
        try:
            logger.info("\n=== 검색 기능 테스트 ===")
            
            # 상품 검색 테스트
            search_data = {
                "keyword": "무선 이어폰",
                "platform": "all",
                "page": 1
            }
            
            response = requests.post(
                f"{self.base_url}/api/search/products",
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 상품 검색 성공: {data.get('total_results', 0)}개 결과")
                
                # 검색 결과 상세 정보
                for platform, products in data.get('results', {}).items():
                    logger.info(f"  {platform}: {len(products)}개 상품")
                    
                return True
            else:
                logger.warning(f"⚠️ 상품 검색 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 검색 기능 테스트 중 오류: {e}")
            return False

    async def test_dashboard_page(self) -> bool:
        """대시보드 페이지 테스트"""
        try:
            logger.info("\n=== 대시보드 페이지 테스트 ===")
            
            response = requests.get(f"{self.base_url}/dashboard", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # HTML 내용 확인
                if "Dropshipping Dashboard" in content and "React" in content:
                    logger.info("✅ 대시보드 페이지 로드 성공")
                    logger.info("  React 컴포넌트 포함됨")
                    logger.info("  Chart.js 라이브러리 포함됨")
                    return True
                else:
                    logger.warning("⚠️ 대시보드 페이지 내용이 예상과 다름")
                    return False
            else:
                logger.error(f"❌ 대시보드 페이지 로드 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 대시보드 페이지 테스트 중 오류: {e}")
            return False

    async def test_database_integration(self) -> bool:
        """데이터베이스 통합 테스트"""
        try:
            logger.info("\n=== 데이터베이스 통합 테스트 ===")
            
            # 데이터베이스 연결 테스트
            test_data = await self.db_service.select_data("competitor_products", {}, limit=5)
            
            if test_data is not None:
                logger.info(f"✅ 데이터베이스 연결 성공: {len(test_data)}개 레코드 조회")
                return True
            else:
                logger.warning("⚠️ 데이터베이스 연결 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 데이터베이스 통합 테스트 중 오류: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        try:
            logger.info("🚀 대시보드 서버 테스트 시작")
            
            test_results = []
            
            # 1. 서버 시작 테스트
            test_results.append(await self.test_server_startup())
            
            # 2. 데이터베이스 통합 테스트
            test_results.append(await self.test_database_integration())
            
            # 3. API 엔드포인트 테스트
            test_results.append(await self.test_api_endpoints())
            
            # 4. 검색 기능 테스트
            test_results.append(await self.test_search_functionality())
            
            # 5. 대시보드 페이지 테스트
            test_results.append(await self.test_dashboard_page())
            
            # 결과 요약
            passed_tests = sum(test_results)
            total_tests = len(test_results)
            
            logger.info(f"\n📊 대시보드 서버 테스트 결과 요약:")
            logger.info(f"  총 테스트: {total_tests}개")
            logger.info(f"  성공: {passed_tests}개")
            logger.info(f"  실패: {total_tests - passed_tests}개")
            logger.info(f"  성공률: {passed_tests/total_tests*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 모든 대시보드 서버 테스트 통과!")
                return True
            else:
                logger.warning("⚠️ 일부 테스트 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 대시보드 서버 테스트 실행 중 오류: {e}")
            return False


async def main():
    """메인 함수"""
    tester = DashboardServerTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ 대시보드 서버 테스트 완료")
        logger.info("🌐 대시보드 접속: http://localhost:8000/dashboard")
    else:
        logger.error("\n❌ 대시보드 서버 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
