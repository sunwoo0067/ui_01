"""
경쟁사 데이터 수집 스케줄러 시스템
"""

import asyncio
import schedule
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger

from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService
from src.services.price_comparison_service import PriceComparisonService
from src.services.database_service import DatabaseService


class CompetitorDataScheduler:
    """경쟁사 데이터 수집 스케줄러"""

    def __init__(self):
        self.coupang_service = CoupangSearchService()
        self.naver_service = NaverSmartStoreSearchService()
        self.price_comparison_service = PriceComparisonService()
        self.db_service = DatabaseService()
        
        # 모니터링 키워드 설정
        self.monitoring_keywords = [
            "무선 이어폰",
            "스마트워치",
            "블루투스 스피커",
            "무선 충전기",
            "USB 케이블",
            "스마트폰 케이스",
            "노트북 가방",
            "게이밍 마우스",
            "키보드",
            "모니터"
        ]
        
        # 플랫폼 설정
        self.platforms = ['coupang', 'naver_smartstore']
        
        # 스케줄 설정
        self.is_running = False

    async def start_scheduler(self):
        """스케줄러 시작"""
        try:
            logger.info("🚀 경쟁사 데이터 수집 스케줄러 시작")
            
            # 스케줄 등록
            schedule.every(30).minutes.do(self._run_data_collection)
            schedule.every(1).hours.do(self._run_price_monitoring)
            schedule.every(6).hours.do(self._run_market_analysis)
            schedule.every().day.at("09:00").do(self._run_daily_report)
            
            self.is_running = True
            
            # 스케줄러 실행
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(60)  # 1분마다 체크
                
        except Exception as e:
            logger.error(f"❌ 스케줄러 실행 중 오류: {e}")
            self.is_running = False

    def stop_scheduler(self):
        """스케줄러 중지"""
        logger.info("⏹️ 경쟁사 데이터 수집 스케줄러 중지")
        self.is_running = False

    async def _run_data_collection(self):
        """데이터 수집 작업 실행"""
        try:
            logger.info("📊 경쟁사 데이터 수집 시작")
            
            total_collected = 0
            
            for keyword in self.monitoring_keywords:
                try:
                    # 쿠팡 데이터 수집
                    coupang_products = await self.coupang_service.search_products(
                        keyword=keyword,
                        page=1,
                        limit=20
                    )
                    
                    if coupang_products:
                        saved_count = await self.coupang_service.save_competitor_products(
                            coupang_products, 
                            keyword
                        )
                        total_collected += saved_count
                        logger.info(f"쿠팡 데이터 수집 완료: {keyword} - {saved_count}개")
                    
                    # 네이버 스마트스토어 데이터 수집
                    naver_products = await self.naver_service.search_products(
                        keyword=keyword,
                        page=1,
                        limit=20
                    )
                    
                    if naver_products:
                        saved_count = await self.naver_service.save_competitor_products(
                            naver_products, 
                            keyword
                        )
                        total_collected += saved_count
                        logger.info(f"네이버 스마트스토어 데이터 수집 완료: {keyword} - {saved_count}개")
                    
                    # 요청 간격 조절 (API 제한 방지)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 데이터 수집 실패: {e}")
                    continue
            
            # 수집 로그 저장
            await self._log_data_collection("data_collection", total_collected)
            
            logger.info(f"📊 경쟁사 데이터 수집 완료: 총 {total_collected}개 상품")
            
        except Exception as e:
            logger.error(f"❌ 데이터 수집 작업 실패: {e}")

    async def _run_price_monitoring(self):
        """가격 모니터링 작업 실행"""
        try:
            logger.info("💰 가격 모니터링 시작")
            
            total_alerts = 0
            
            for keyword in self.monitoring_keywords:
                try:
                    # 가격 변동 모니터링
                    alerts = await self.price_comparison_service.monitor_price_changes(
                        keyword=keyword,
                        alert_threshold=10.0
                    )
                    
                    if alerts:
                        total_alerts += len(alerts)
                        logger.info(f"가격 변동 알림: {keyword} - {len(alerts)}개")
                        
                        # 알림 처리
                        await self._process_price_alerts(alerts)
                    
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 가격 모니터링 실패: {e}")
                    continue
            
            logger.info(f"💰 가격 모니터링 완료: 총 {total_alerts}개 알림")
            
        except Exception as e:
            logger.error(f"❌ 가격 모니터링 작업 실패: {e}")

    async def _run_market_analysis(self):
        """시장 분석 작업 실행"""
        try:
            logger.info("📈 시장 분석 시작")
            
            analysis_count = 0
            
            for keyword in self.monitoring_keywords[:5]:  # 상위 5개 키워드만 분석
                try:
                    # 시장 인사이트 분석
                    insights = await self.price_comparison_service.get_market_insights(
                        keyword=keyword,
                        days=7
                    )
                    
                    if insights and insights.get('insights'):
                        analysis_count += 1
                        logger.info(f"시장 분석 완료: {keyword}")
                    
                    # 네이버 스마트스토어 경쟁사 동향 분석
                    trends = await self.naver_service.analyze_competitor_trends(
                        keyword=keyword,
                        days=7
                    )
                    
                    if trends:
                        logger.info(f"경쟁사 동향 분석 완료: {keyword}")
                    
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 시장 분석 실패: {e}")
                    continue
            
            logger.info(f"📈 시장 분석 완료: {analysis_count}개 키워드")
            
        except Exception as e:
            logger.error(f"❌ 시장 분석 작업 실패: {e}")

    async def _run_daily_report(self):
        """일일 리포트 생성"""
        try:
            logger.info("📋 일일 리포트 생성 시작")
            
            # 리포트 데이터 수집
            report_data = await self._generate_daily_report()
            
            # 리포트 저장
            await self._save_daily_report(report_data)
            
            logger.info("📋 일일 리포트 생성 완료")
            
        except Exception as e:
            logger.error(f"❌ 일일 리포트 생성 실패: {e}")

    async def _process_price_alerts(self, alerts: List[Dict[str, Any]]):
        """가격 알림 처리"""
        try:
            for alert in alerts:
                # 알림 로그 저장
                alert_log = {
                    "keyword": alert.get('keyword', ''),
                    "platform": alert['platform'],
                    "product_id": alert['product_id'],
                    "old_price": alert['old_price'],
                    "new_price": alert['new_price'],
                    "price_change": alert['price_change'],
                    "price_change_rate": alert['price_change_rate'],
                    "alert_message": f"가격 변동: {alert['old_price']:,}원 → {alert['new_price']:,}원 ({alert['price_change_rate']:.1f}%)",
                    "notification_sent": False,
                    "triggered_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db_service.insert_data("price_alert_logs", alert_log)
                
                # 실제 알림 발송 (이메일, 웹훅 등)
                await self._send_notification(alert)
                
        except Exception as e:
            logger.error(f"❌ 가격 알림 처리 실패: {e}")

    async def _send_notification(self, alert: Dict[str, Any]):
        """알림 발송"""
        try:
            # 여기서 실제 알림 발송 로직 구현
            # 이메일, 슬랙, 디스코드 등
            
            message = f"""
🚨 가격 변동 알림

상품: {alert.get('product_id', 'N/A')}
플랫폼: {alert['platform']}
가격 변동: {alert['old_price']:,}원 → {alert['new_price']:,}원
변동률: {alert['price_change_rate']:.1f}%
시간: {alert['timestamp']}
            """
            
            logger.info(f"알림 발송: {message}")
            
        except Exception as e:
            logger.error(f"❌ 알림 발송 실패: {e}")

    async def _generate_daily_report(self) -> Dict[str, Any]:
        """일일 리포트 데이터 생성"""
        try:
            # 어제 데이터 조회
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            today = datetime.now(timezone.utc)
            
            # 수집된 상품 수
            collected_products = await self.db_service.select_data(
                "competitor_products",
                {
                    "collected_at__gte": yesterday.isoformat(),
                    "collected_at__lt": today.isoformat()
                }
            )
            
            # 가격 변동 수
            price_changes = await self.db_service.select_data(
                "price_history",
                {
                    "timestamp__gte": yesterday.isoformat(),
                    "timestamp__lt": today.isoformat()
                }
            )
            
            # 플랫폼별 통계
            platform_stats = {}
            for platform in self.platforms:
                platform_products = [p for p in collected_products if p['platform'] == platform]
                platform_stats[platform] = len(platform_products)
            
            # 키워드별 통계
            keyword_stats = {}
            for keyword in self.monitoring_keywords:
                keyword_products = [p for p in collected_products if p.get('search_keyword') == keyword]
                keyword_stats[keyword] = len(keyword_products)
            
            return {
                "report_date": yesterday.strftime("%Y-%m-%d"),
                "total_products_collected": len(collected_products),
                "total_price_changes": len(price_changes),
                "platform_statistics": platform_stats,
                "keyword_statistics": keyword_stats,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 일일 리포트 데이터 생성 실패: {e}")
            return {}

    async def _save_daily_report(self, report_data: Dict[str, Any]):
        """일일 리포트 저장"""
        try:
            if report_data:
                await self.db_service.insert_data("daily_reports", report_data)
                logger.info(f"일일 리포트 저장 완료: {report_data.get('report_date')}")
            
        except Exception as e:
            logger.error(f"❌ 일일 리포트 저장 실패: {e}")

    async def _log_data_collection(self, collection_type: str, items_collected: int):
        """데이터 수집 로그 저장"""
        try:
            log_data = {
                "platform": "all",
                "collection_type": collection_type,
                "success": True,
                "items_collected": items_collected,
                "collected_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db_service.insert_data("data_collection_logs", log_data)
            
        except Exception as e:
            logger.error(f"❌ 데이터 수집 로그 저장 실패: {e}")

    async def run_manual_collection(self, keywords: List[str] = None):
        """수동 데이터 수집 실행"""
        try:
            logger.info("🔧 수동 데이터 수집 시작")
            
            if keywords is None:
                keywords = self.monitoring_keywords
            
            await self._run_data_collection()
            
            logger.info("🔧 수동 데이터 수집 완료")
            
        except Exception as e:
            logger.error(f"❌ 수동 데이터 수집 실패: {e}")

    async def run_manual_analysis(self, keywords: List[str] = None):
        """수동 시장 분석 실행"""
        try:
            logger.info("🔧 수동 시장 분석 시작")
            
            if keywords is None:
                keywords = self.monitoring_keywords[:5]
            
            await self._run_market_analysis()
            
            logger.info("🔧 수동 시장 분석 완료")
            
        except Exception as e:
            logger.error(f"❌ 수동 시장 분석 실패: {e}")


# 전역 인스턴스
competitor_data_scheduler = CompetitorDataScheduler()


async def main():
    """메인 함수 - 스케줄러 실행"""
    scheduler = CompetitorDataScheduler()
    
    try:
        await scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 스케줄러가 중지되었습니다.")
        scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"스케줄러 실행 중 오류: {e}")
        scheduler.stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
