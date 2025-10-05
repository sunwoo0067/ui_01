"""
REST API 서버 - 외부 시스템 연동을 위한 확장 API

기존 대시보드 API를 확장하여 더 포괄적인 REST API를 제공합니다.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from loguru import logger
import uvicorn

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import DatabaseService
from src.services.coupang_search_service import CoupangSearchService
from src.services.naver_smartstore_search_service import NaverSmartStoreSearchService
from src.services.elevenstreet_search_service import ElevenStreetSearchService
from src.services.gmarket_search_service import GmarketSearchService
from src.services.auction_search_service import AuctionSearchService
from src.services.unified_marketplace_search_service import UnifiedMarketplaceSearchService
from src.services.price_comparison_service import PriceComparisonService
from src.services.competitor_data_scheduler import CompetitorDataScheduler
from src.services.ai_price_prediction_service import AIPricePredictionService
from src.services.ownerclan_data_collector import OwnerClanDataCollector
from src.services.ownerclan_data_storage import OwnerClanDataStorage
from src.services.transaction_system import TransactionSystem
from src.services.order_management_service import OrderManagementService
from src.services.inventory_sync_service import InventorySyncService
from src.services.supplier_account_manager import SupplierAccountManager


# FastAPI 앱 생성
app = FastAPI(
    title="Dropshipping Automation REST API",
    description="드롭쉬핑 자동화 시스템을 위한 포괄적인 REST API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
security = HTTPBearer(auto_error=False)

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

def get_ai_prediction_service():
    return AIPricePredictionService()

def get_unified_service():
    return UnifiedMarketplaceSearchService()

def get_price_comparison_service():
    return PriceComparisonService()

def get_scheduler_service():
    return CompetitorDataScheduler()

def get_ownerclan_collector():
    return OwnerClanDataCollector()

def get_ownerclan_storage():
    return OwnerClanDataStorage()

def get_transaction_system():
    return TransactionSystem()

def get_order_management():
    return OrderManagementService()

def get_inventory_sync():
    return InventorySyncService()

def get_supplier_manager():
    return SupplierAccountManager()


# Pydantic 모델들
class ProductSearchRequest(BaseModel):
    keyword: str = Field(..., description="검색 키워드")
    page: int = Field(1, ge=1, description="페이지 번호")
    platform: Optional[str] = Field(None, description="특정 플랫폼 검색")
    category: Optional[str] = Field(None, description="카테고리 필터")
    min_price: Optional[int] = Field(None, ge=0, description="최소 가격")
    max_price: Optional[int] = Field(None, ge=0, description="최대 가격")

class ProductData(BaseModel):
    name: str
    price: int
    seller: str
    product_url: str
    platform: str
    original_price: Optional[int] = None
    discount_rate: Optional[int] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    shipping_info: Optional[str] = None
    category: Optional[str] = None

class PricePredictionRequest(BaseModel):
    product_data: Dict[str, Any] = Field(..., description="상품 데이터")
    category: Optional[str] = Field(None, description="카테고리")

class OrderInput(BaseModel):
    products: List[Dict[str, Any]] = Field(..., description="주문 상품 목록")
    recipient: Dict[str, Any] = Field(..., description="수령인 정보")
    note: Optional[str] = Field(None, description="주문 메모")
    seller_note: Optional[str] = Field(None, description="판매자 메모")
    orderer_note: Optional[str] = Field(None, description="주문자 메모")

class SupplierAccountRequest(BaseModel):
    supplier_code: str = Field(..., description="공급사 코드")
    account_name: str = Field(..., description="계정명")
    credentials: Dict[str, Any] = Field(..., description="인증 정보")
    is_active: bool = Field(True, description="활성 상태")

class BatchOperationRequest(BaseModel):
    operation: str = Field(..., description="작업 유형")
    parameters: Dict[str, Any] = Field(..., description="작업 매개변수")
    target_ids: Optional[List[str]] = Field(None, description="대상 ID 목록")

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


# 인증 미들웨어 (간단한 구현)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증 (개발용 간단 구현)"""
    if not credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
    
    # 실제 환경에서는 JWT 토큰 검증 로직 구현
    token = credentials.credentials
    if token != "dev_token_123":  # 개발용 토큰
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    
    return {"user_id": "dev_user", "role": "admin"}


# 기본 엔드포인트
@app.get("/", response_model=APIResponse)
async def root():
    """API 루트 엔드포인트"""
    return APIResponse(
        success=True,
        message="Dropshipping Automation REST API",
        data={
            "version": "2.0.0",
            "status": "running",
            "endpoints": {
                "products": "/api/v2/products",
                "search": "/api/v2/search",
                "ai": "/api/v2/ai",
                "orders": "/api/v2/orders",
                "suppliers": "/api/v2/suppliers",
                "analytics": "/api/v2/analytics"
            }
        }
    )

@app.get("/health", response_model=APIResponse)
async def health_check():
    """헬스 체크"""
    return APIResponse(
        success=True,
        message="API 서버가 정상적으로 작동 중입니다",
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running"
        }
    )


# 상품 관련 API
@app.get("/api/v2/products", response_model=APIResponse)
async def get_products(
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    platform: Optional[str] = Query(None, description="플랫폼 필터"),
    db_service: DatabaseService = Depends(get_db_service),
    current_user: dict = Depends(verify_token)
):
    """상품 목록 조회"""
    try:
        filters = {}
        if category:
            filters["category"] = category
        if platform:
            filters["platform"] = platform
        
        products = await db_service.select_data(
            "competitor_products",
            filters,
            limit=limit,
            offset=offset
        )
        
        return APIResponse(
            success=True,
            message=f"{len(products)}개의 상품을 조회했습니다",
            data={
                "products": products,
                "total": len(products),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/products/{product_id}", response_model=APIResponse)
async def get_product(
    product_id: str = Path(..., description="상품 ID"),
    db_service: DatabaseService = Depends(get_db_service),
    current_user: dict = Depends(verify_token)
):
    """특정 상품 조회"""
    try:
        product = await db_service.select_data(
            "competitor_products",
            {"id": product_id},
            limit=1
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        
        return APIResponse(
            success=True,
            message="상품 조회 성공",
            data=product[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 검색 관련 API
@app.post("/api/v2/search", response_model=APIResponse)
async def search_products(
    request: ProductSearchRequest,
    unified_service: UnifiedMarketplaceSearchService = Depends(get_unified_service),
    current_user: dict = Depends(verify_token)
):
    """상품 검색"""
    try:
        logger.info(f"상품 검색 요청: {request.keyword}")
        
        if request.platform:
            # 특정 플랫폼 검색
            search_results = await unified_service.search_single_platform(
                platform=request.platform,
                keyword=request.keyword,
                page=request.page
            )
        else:
            # 전체 플랫폼 검색
            search_results = await unified_service.search_all_platforms(
                keyword=request.keyword,
                page=request.page
            )
        
        # 가격 필터 적용
        filtered_results = {}
        for platform, products in search_results.items():
            filtered_products = []
            for product in products:
                if request.min_price and product.price < request.min_price:
                    continue
                if request.max_price and product.price > request.max_price:
                    continue
                if request.category and product.category != request.category:
                    continue
                filtered_products.append(product)
            filtered_results[platform] = filtered_products
        
        return APIResponse(
            success=True,
            message=f"'{request.keyword}' 검색 완료",
            data={
                "keyword": request.keyword,
                "page": request.page,
                "platform": request.platform,
                "results": {platform: [product.dict() for product in products] 
                           for platform, products in filtered_results.items()},
                "total_results": sum(len(products) for products in filtered_results.values())
            }
        )
        
    except Exception as e:
        logger.error(f"상품 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/search/suggestions", response_model=APIResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="검색어"),
    limit: int = Query(10, ge=1, le=20, description="제안 개수"),
    db_service: DatabaseService = Depends(get_db_service),
    current_user: dict = Depends(verify_token)
):
    """검색 제안"""
    try:
        # 간단한 검색 제안 구현
        suggestions = await db_service.select_data(
            "competitor_products",
            {"name": {"ilike": f"%{q}%"}},
            limit=limit
        )
        
        suggestion_list = [product["name"] for product in suggestions]
        
        return APIResponse(
            success=True,
            message=f"'{q}'에 대한 검색 제안",
            data={
                "query": q,
                "suggestions": suggestion_list,
                "count": len(suggestion_list)
            }
        )
        
    except Exception as e:
        logger.error(f"검색 제안 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI 예측 관련 API
@app.post("/api/v2/ai/predict", response_model=APIResponse)
async def predict_price(
    request: PricePredictionRequest,
    ai_service: AIPricePredictionService = Depends(get_ai_prediction_service),
    current_user: dict = Depends(verify_token)
):
    """AI 가격 예측"""
    try:
        logger.info("AI 가격 예측 요청")
        
        predictions = await ai_service.predict_price(
            request.product_data,
            request.category
        )
        
        return APIResponse(
            success=True,
            message="가격 예측 완료",
            data={
                "predictions": [
                    {
                        "model": p.model_name,
                        "predicted_price": p.predicted_price,
                        "confidence": p.confidence_score,
                        "features_used": p.features_used
                    }
                    for p in predictions
                ],
                "best_prediction": {
                    "model": predictions[0].model_name if predictions else None,
                    "price": predictions[0].predicted_price if predictions else None,
                    "confidence": predictions[0].confidence_score if predictions else None
                }
            }
        )
        
    except Exception as e:
        logger.error(f"AI 가격 예측 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/ai/strategy", response_model=APIResponse)
async def get_pricing_strategy(
    request: PricePredictionRequest,
    ai_service: AIPricePredictionService = Depends(get_ai_prediction_service),
    current_user: dict = Depends(verify_token)
):
    """가격 전략 제안"""
    try:
        logger.info("가격 전략 분석 요청")
        
        strategy_result = await ai_service.get_optimal_pricing_strategy(
            request.product_data,
            request.category
        )
        
        return APIResponse(
            success=True,
            message="가격 전략 분석 완료",
            data=strategy_result
        )
        
    except Exception as e:
        logger.error(f"가격 전략 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/ai/trends", response_model=APIResponse)
async def get_market_trends(
    category: Optional[str] = Query(None, description="카테고리"),
    ai_service: AIPricePredictionService = Depends(get_ai_prediction_service),
    current_user: dict = Depends(verify_token)
):
    """시장 트렌드 분석"""
    try:
        logger.info(f"시장 트렌드 분석 요청 - 카테고리: {category}")
        
        market_trend = await ai_service.analyze_market_trend(category)
        
        return APIResponse(
            success=True,
            message="시장 트렌드 분석 완료",
            data={
                "trend_direction": market_trend.trend_direction,
                "trend_strength": market_trend.trend_strength,
                "volatility": market_trend.volatility,
                "seasonal_pattern": market_trend.seasonal_pattern,
                "competitor_count": market_trend.competitor_count,
                "price_range": {
                    "min": market_trend.price_range[0],
                    "max": market_trend.price_range[1]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"시장 트렌드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 주문 관련 API
@app.post("/api/v2/orders", response_model=APIResponse)
async def create_order(
    order_data: OrderInput,
    transaction_system: TransactionSystem = Depends(get_transaction_system),
    current_user: dict = Depends(verify_token)
):
    """주문 생성"""
    try:
        logger.info("주문 생성 요청")
        
        # OrderInput을 TransactionSystem이 기대하는 형식으로 변환
        from services.transaction_system import OrderInput as TSOrderInput, ProductInput, RecipientInput
        
        products = [
            ProductInput(
                item_key=product["item_key"],
                quantity=product["quantity"],
                option_attributes=product.get("option_attributes", [])
            )
            for product in order_data.products
        ]
        
        recipient = RecipientInput(
            name=order_data.recipient["name"],
            phone=order_data.recipient["phone"],
            address=order_data.recipient["address"],
            postal_code=order_data.recipient["postal_code"],
            city=order_data.recipient["city"],
            district=order_data.recipient["district"],
            detail_address=order_data.recipient["detail_address"]
        )
        
        ts_order_input = TSOrderInput(
            products=products,
            recipient=recipient,
            note=order_data.note,
            seller_note=order_data.seller_note,
            orderer_note=order_data.orderer_note
        )
        
        result = await transaction_system.create_order(ts_order_input)
        
        if result.success:
            return APIResponse(
                success=True,
                message="주문 생성 성공",
                data={
                    "order_id": result.order_id,
                    "status": result.status,
                    "message": result.message
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result.error)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주문 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/orders", response_model=APIResponse)
async def get_orders(
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    status: Optional[str] = Query(None, description="주문 상태"),
    db_service: DatabaseService = Depends(get_db_service),
    current_user: dict = Depends(verify_token)
):
    """주문 목록 조회"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        
        orders = await db_service.select_data(
            "local_orders",
            filters,
            limit=limit,
            offset=offset
        )
        
        return APIResponse(
            success=True,
            message=f"{len(orders)}개의 주문을 조회했습니다",
            data={
                "orders": orders,
                "total": len(orders),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"주문 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 공급사 관련 API
@app.get("/api/v2/suppliers", response_model=APIResponse)
async def get_suppliers(
    supplier_manager: SupplierAccountManager = Depends(get_supplier_manager),
    current_user: dict = Depends(verify_token)
):
    """공급사 목록 조회"""
    try:
        suppliers = await supplier_manager.list_supplier_accounts()
        
        return APIResponse(
            success=True,
            message=f"{len(suppliers)}개의 공급사를 조회했습니다",
            data={
                "suppliers": suppliers,
                "count": len(suppliers)
            }
        )
        
    except Exception as e:
        logger.error(f"공급사 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/suppliers", response_model=APIResponse)
async def create_supplier(
    supplier_data: SupplierAccountRequest,
    supplier_manager: SupplierAccountManager = Depends(get_supplier_manager),
    current_user: dict = Depends(verify_token)
):
    """공급사 계정 생성"""
    try:
        logger.info(f"공급사 계정 생성 요청: {supplier_data.supplier_code}")
        
        result = await supplier_manager.create_supplier_account(
            supplier_code=supplier_data.supplier_code,
            account_name=supplier_data.account_name,
            credentials=supplier_data.credentials,
            is_active=supplier_data.is_active
        )
        
        if result:
            return APIResponse(
                success=True,
                message="공급사 계정 생성 성공",
                data={"supplier_code": supplier_data.supplier_code}
            )
        else:
            raise HTTPException(status_code=400, detail="공급사 계정 생성 실패")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공급사 계정 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 분석 관련 API
@app.get("/api/v2/analytics/dashboard", response_model=APIResponse)
async def get_dashboard_analytics(
    period: str = Query("7d", description="분석 기간 (1d, 7d, 30d)"),
    db_service: DatabaseService = Depends(get_db_service),
    current_user: dict = Depends(verify_token)
):
    """대시보드 분석 데이터"""
    try:
        # 기간 계산
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # 기본 통계 조회
        total_products = await db_service.select_data("competitor_products", {})
        total_orders = await db_service.select_data("local_orders", {})
        
        analytics_data = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "statistics": {
                "total_products": len(total_products),
                "total_orders": len(total_orders),
                "active_suppliers": 0,  # 실제 구현 필요
                "platforms_monitored": 5
            },
            "trends": {
                "product_growth": 0,  # 실제 구현 필요
                "order_growth": 0,    # 실제 구현 필요
                "price_changes": 0    # 실제 구현 필요
            }
        }
        
        return APIResponse(
            success=True,
            message="대시보드 분석 데이터 조회 완료",
            data=analytics_data
        )
        
    except Exception as e:
        logger.error(f"대시보드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 배치 작업 API
@app.post("/api/v2/batch", response_model=APIResponse)
async def execute_batch_operation(
    request: BatchOperationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token)
):
    """배치 작업 실행"""
    try:
        logger.info(f"배치 작업 요청: {request.operation}")
        
        # 배치 작업 처리
        if request.operation == "data_collection":
            background_tasks.add_task(
                execute_data_collection,
                request.parameters
            )
            message = "데이터 수집 작업이 백그라운드에서 시작되었습니다"
            
        elif request.operation == "price_analysis":
            background_tasks.add_task(
                execute_price_analysis,
                request.parameters
            )
            message = "가격 분석 작업이 백그라운드에서 시작되었습니다"
            
        elif request.operation == "model_training":
            background_tasks.add_task(
                execute_model_training,
                request.parameters
            )
            message = "모델 훈련 작업이 백그라운드에서 시작되었습니다"
            
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 작업 유형입니다")
        
        return APIResponse(
            success=True,
            message=message,
            data={
                "operation": request.operation,
                "status": "started",
                "parameters": request.parameters
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 작업 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 백그라운드 작업 함수들
async def execute_data_collection(parameters: Dict[str, Any]):
    """데이터 수집 백그라운드 작업"""
    try:
        logger.info("데이터 수집 백그라운드 작업 시작")
        # 실제 데이터 수집 로직 구현
        await asyncio.sleep(1)  # 시뮬레이션
        logger.info("데이터 수집 백그라운드 작업 완료")
    except Exception as e:
        logger.error(f"데이터 수집 백그라운드 작업 실패: {e}")

async def execute_price_analysis(parameters: Dict[str, Any]):
    """가격 분석 백그라운드 작업"""
    try:
        logger.info("가격 분석 백그라운드 작업 시작")
        # 실제 가격 분석 로직 구현
        await asyncio.sleep(1)  # 시뮬레이션
        logger.info("가격 분석 백그라운드 작업 완료")
    except Exception as e:
        logger.error(f"가격 분석 백그라운드 작업 실패: {e}")

async def execute_model_training(parameters: Dict[str, Any]):
    """모델 훈련 백그라운드 작업"""
    try:
        logger.info("모델 훈련 백그라운드 작업 시작")
        # 실제 모델 훈련 로직 구현
        await asyncio.sleep(1)  # 시뮬레이션
        logger.info("모델 훈련 백그라운드 작업 완료")
    except Exception as e:
        logger.error(f"모델 훈련 백그라운드 작업 실패: {e}")


# 서버 시작
if __name__ == "__main__":
    logger.info("🚀 REST API 서버 시작")
    uvicorn.run(
        "rest_api_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
