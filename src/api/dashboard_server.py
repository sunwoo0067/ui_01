"""
FastAPI 백엔드 서버 - 대시보드 API
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from services.coupang_search_service import CoupangSearchService
from services.naver_smartstore_search_service import NaverSmartStoreSearchService
from services.elevenstreet_search_service import ElevenStreetSearchService
from services.gmarket_search_service import GmarketSearchService
from services.auction_search_service import AuctionSearchService
from services.unified_marketplace_search_service import UnifiedMarketplaceSearchService
from services.price_comparison_service import PriceComparisonService
from services.competitor_data_scheduler import CompetitorDataScheduler


# FastAPI 앱 생성
app = FastAPI(
    title="Dropshipping Dashboard API",
    description="드롭쉬핑 자동화 시스템 대시보드 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 의존성 주입
def get_db_service():
    return DatabaseService()

def get_coupang_service():
    return CoupangSearchService()

def get_naver_service():
    return NaverSmartStoreSearchService()

def get_elevenstreet_service():
    return ElevenStreetSearchService()

def get_gmarket_service():
    return GmarketSearchService()

def get_auction_service():
    return AuctionSearchService()

def get_unified_service():
    return UnifiedMarketplaceSearchService()

def get_price_comparison_service():
    return PriceComparisonService()

def get_scheduler():
    return CompetitorDataScheduler()


# Pydantic 모델들
class ProductSearchRequest(BaseModel):
    keyword: str
    page: int = 1
    platform: str = "all"  # coupang, naver_smartstore, 11st, gmarket, auction, all

class PriceComparisonRequest(BaseModel):
    keyword: str
    our_product_id: str
    our_price: int
    platforms: List[str] = ["coupang", "naver_smartstore"]

class MarketInsightsRequest(BaseModel):
    keyword: str
    days: int = 7

class DashboardStats(BaseModel):
    total_products: int
    total_price_changes: int
    active_alerts: int
    platforms: Dict[str, int]
    keywords: Dict[str, int]
    last_updated: datetime


# API 엔드포인트들

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Dropshipping Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db_service: DatabaseService = Depends(get_db_service)):
    """대시보드 통계 조회"""
    try:
        # 최근 24시간 데이터 조회
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        # 총 상품 수
        total_products = await db_service.select_data(
            "competitor_products",
            {"is_active": True}
        )
        
        # 가격 변동 수
        price_changes = await db_service.select_data(
            "price_history",
            {"timestamp__gte": yesterday.isoformat()}
        )
        
        # 활성 알림 수
        active_alerts = await db_service.select_data(
            "price_alerts",
            {"is_active": True}
        )
        
        # 플랫폼별 통계
        platforms = {}
        for platform in ["coupang", "naver_smartstore"]:
            platform_products = [p for p in total_products if p.get('platform') == platform]
            platforms[platform] = len(platform_products)
        
        # 키워드별 통계 (상위 10개)
        keyword_stats = {}
        for product in total_products:
            keyword = product.get('search_keyword', 'Unknown')
            keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
        
        # 상위 10개 키워드만 반환
        top_keywords = dict(sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return DashboardStats(
            total_products=len(total_products),
            total_price_changes=len(price_changes),
            active_alerts=len(active_alerts),
            platforms=platforms,
            keywords=top_keywords,
            last_updated=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/products")
async def search_products(
    request: ProductSearchRequest,
    unified_service: UnifiedMarketplaceSearchService = Depends(get_unified_service)
):
    """상품 검색 (통합 마켓플레이스)"""
    try:
        if request.platform == "all":
            # 모든 플랫폼에서 검색
            results = await unified_service.search_all_platforms(
                keyword=request.keyword,
                page=request.page
            )
        else:
            # 특정 플랫폼에서만 검색
            products = await unified_service.search_single_platform(
                keyword=request.keyword,
                platform=request.platform,
                page=request.page
            )
            results = {request.platform: products}
        
        return {
            "keyword": request.keyword,
            "page": request.page,
            "platform": request.platform,
            "results": {platform: [product.dict() for product in products] 
                       for platform, products in results.items()},
            "total_results": sum(len(products) for products in results.values())
        }
        
    except Exception as e:
        logger.error(f"상품 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/price/comparison")
async def compare_prices(
    request: PriceComparisonRequest,
    price_service: PriceComparisonService = Depends(get_price_comparison_service)
):
    """가격 비교 분석"""
    try:
        result = await price_service.compare_prices(
            keyword=request.keyword,
            our_product_id=request.our_product_id,
            our_price=request.our_price,
            platforms=request.platforms
        )
        
        return {
            "keyword": request.keyword,
            "our_product_id": request.our_product_id,
            "our_price": request.our_price,
            "price_analysis": result.price_analysis,
            "recommendations": result.recommendations,
            "competitor_products": result.competitor_products
        }
        
    except Exception as e:
        logger.error(f"가격 비교 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/market/insights")
async def get_market_insights(
    request: MarketInsightsRequest,
    price_service: PriceComparisonService = Depends(get_price_comparison_service)
):
    """시장 인사이트 분석"""
    try:
        insights = await price_service.get_market_insights(
            keyword=request.keyword,
            days=request.days
        )
        
        return {
            "keyword": request.keyword,
            "days": request.days,
            "insights": insights.get('insights', {}),
            "generated_at": insights.get('generated_at')
        }
        
    except Exception as e:
        logger.error(f"시장 인사이트 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/recent")
async def get_recent_products(
    limit: int = 50,
    db_service: DatabaseService = Depends(get_db_service)
):
    """최근 수집된 상품 조회"""
    try:
        products = await db_service.select_data(
            "competitor_products",
            {"is_active": True},
            limit=limit
        )
        
        # 최신순으로 정렬
        products.sort(key=lambda x: x.get('collected_at', ''), reverse=True)
        
        return {
            "products": products,
            "total": len(products)
        }
        
    except Exception as e:
        logger.error(f"최근 상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/price/history")
async def get_price_history(
    product_id: Optional[str] = None,
    keyword: Optional[str] = None,
    days: int = 7,
    db_service: DatabaseService = Depends(get_db_service)
):
    """가격 변동 이력 조회"""
    try:
        filters = {}
        
        if product_id:
            filters["product_id"] = product_id
        if keyword:
            filters["search_keyword"] = keyword
        
        # 날짜 필터
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        filters["timestamp__gte"] = since_date.isoformat()
        
        price_history = await db_service.select_data(
            "price_history",
            filters
        )
        
        # 시간순으로 정렬
        price_history.sort(key=lambda x: x.get('timestamp', ''))
        
        return {
            "price_history": price_history,
            "total": len(price_history),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"가격 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/active")
async def get_active_alerts(
    db_service: DatabaseService = Depends(get_db_service)
):
    """활성 알림 조회"""
    try:
        alerts = await db_service.select_data(
            "price_alerts",
            {"is_active": True}
        )
        
        return {
            "alerts": alerts,
            "total": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"활성 알림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/start")
async def start_scheduler(
    background_tasks: BackgroundTasks,
    scheduler: CompetitorDataScheduler = Depends(get_scheduler)
):
    """스케줄러 시작"""
    try:
        background_tasks.add_task(scheduler.start_scheduler)
        return {"message": "스케줄러가 시작되었습니다"}
        
    except Exception as e:
        logger.error(f"스케줄러 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/stop")
async def stop_scheduler(
    scheduler: CompetitorDataScheduler = Depends(get_scheduler)
):
    """스케줄러 중지"""
    try:
        scheduler.stop_scheduler()
        return {"message": "스케줄러가 중지되었습니다"}
        
    except Exception as e:
        logger.error(f"스케줄러 중지 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collection/manual")
async def manual_collection(
    keywords: List[str],
    background_tasks: BackgroundTasks,
    scheduler: CompetitorDataScheduler = Depends(get_scheduler)
):
    """수동 데이터 수집"""
    try:
        background_tasks.add_task(scheduler.run_manual_collection, keywords)
        return {"message": f"수동 데이터 수집이 시작되었습니다: {keywords}"}
        
    except Exception as e:
        logger.error(f"수동 데이터 수집 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/supported")
async def get_supported_platforms(
    unified_service: UnifiedMarketplaceSearchService = Depends(get_unified_service)
):
    """지원하는 플랫폼 목록 조회"""
    try:
        platforms = unified_service.get_supported_platforms()
        return {"platforms": platforms, "count": len(platforms)}
        
    except Exception as e:
        logger.error(f"지원 플랫폼 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/status")
async def get_platform_status(
    unified_service: UnifiedMarketplaceSearchService = Depends(get_unified_service)
):
    """플랫폼 상태 확인"""
    try:
        status = await unified_service.get_platform_status()
        return {"platform_status": status}
        
    except Exception as e:
        logger.error(f"플랫폼 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/unified")
async def unified_search(
    request: ProductSearchRequest,
    unified_service: UnifiedMarketplaceSearchService = Depends(get_unified_service)
):
    """통합 마켓플레이스 검색 및 가격 비교"""
    try:
        # 검색 실행
        search_results = await unified_service.search_all_platforms(
            keyword=request.keyword,
            page=request.page
        )
        
        # 가격 비교 분석
        comparison_result = await unified_service.get_price_comparison(
            keyword=request.keyword
        )
        
        return {
            "keyword": request.keyword,
            "page": request.page,
            "search_results": {platform: [product.dict() for product in products] 
                             for platform, products in search_results.items()},
            "price_comparison": comparison_result,
            "total_results": sum(len(products) for products in search_results.values())
        }
        
    except Exception as e:
        logger.error(f"통합 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/recent")
async def get_recent_analysis(
    limit: int = 20,
    db_service: DatabaseService = Depends(get_db_service)
):
    """최근 분석 결과 조회"""
    try:
        analysis_results = await db_service.select_data(
            "competitor_analysis",
            {},
            limit=limit
        )
        
        # 최신순으로 정렬
        analysis_results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "analysis_results": analysis_results,
            "total": len(analysis_results)
        }
        
    except Exception as e:
        logger.error(f"최근 분석 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 정적 파일 서빙 (React 앱)
@app.get("/dashboard")
async def dashboard():
    """대시보드 페이지"""
    return FileResponse("src/api/dashboard.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
