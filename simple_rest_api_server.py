"""
간단한 REST API 테스트 서버
"""

import asyncio
import sys
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from loguru import logger
import uvicorn

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# FastAPI 앱 생성
app = FastAPI(
    title="Simple REST API Test Server",
    description="간단한 REST API 테스트 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
security = HTTPBearer(auto_error=False)

# Pydantic 모델
class APIResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}

# 인증 미들웨어
async def verify_token(credentials = Depends(security)):
    """토큰 검증"""
    if not credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
    
    token = credentials.credentials
    if token != "dev_token_123":
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    
    return {"user_id": "dev_user", "role": "admin"}

# 기본 엔드포인트
@app.get("/")
async def root():
    """API 루트"""
    return APIResponse(
        success=True,
        message="Simple REST API Test Server",
        data={
            "version": "1.0.0",
            "status": "running",
            "endpoints": ["/health", "/api/v2/products", "/api/v2/search"]
        }
    )

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return APIResponse(
        success=True,
        message="서버가 정상적으로 작동 중입니다",
        data={
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

# 상품 관련 API
@app.get("/api/v2/products")
async def get_products(current_user: dict = Depends(verify_token)):
    """상품 목록 조회"""
    return APIResponse(
        success=True,
        message="상품 목록 조회 성공",
        data={
            "products": [
                {
                    "id": "product_001",
                    "name": "테스트 상품",
                    "price": 50000,
                    "platform": "coupang"
                }
            ],
            "total": 1
        }
    )

@app.get("/api/v2/products/{product_id}")
async def get_product(product_id: str, current_user: dict = Depends(verify_token)):
    """특정 상품 조회"""
    return APIResponse(
        success=True,
        message="상품 조회 성공",
        data={
            "id": product_id,
            "name": f"상품 {product_id}",
            "price": 50000,
            "platform": "coupang"
        }
    )

# 검색 관련 API
@app.post("/api/v2/search")
async def search_products(search_data: dict, current_user: dict = Depends(verify_token)):
    """상품 검색"""
    return APIResponse(
        success=True,
        message="검색 완료",
        data={
            "keyword": search_data.get("keyword", ""),
            "results": [
                {
                    "name": "검색 결과 상품",
                    "price": 50000,
                    "platform": "coupang"
                }
            ],
            "total_results": 1
        }
    )

@app.get("/api/v2/search/suggestions")
async def get_search_suggestions(q: str, current_user: dict = Depends(verify_token)):
    """검색 제안"""
    return APIResponse(
        success=True,
        message="검색 제안 완료",
        data={
            "query": q,
            "suggestions": [f"{q} 관련 상품 1", f"{q} 관련 상품 2"],
            "count": 2
        }
    )

# AI 관련 API
@app.post("/api/v2/ai/predict")
async def predict_price(prediction_data: dict, current_user: dict = Depends(verify_token)):
    """AI 가격 예측"""
    return APIResponse(
        success=True,
        message="가격 예측 완료",
        data={
            "predictions": [
                {
                    "model": "test_model",
                    "predicted_price": 52000,
                    "confidence": 0.85
                }
            ],
            "best_prediction": {
                "model": "test_model",
                "price": 52000,
                "confidence": 0.85
            }
        }
    )

@app.post("/api/v2/ai/strategy")
async def get_pricing_strategy(strategy_data: dict, current_user: dict = Depends(verify_token)):
    """가격 전략 제안"""
    return APIResponse(
        success=True,
        message="가격 전략 분석 완료",
        data={
            "recommended_price": 52000,
            "strategy": "competitive",
            "confidence": 0.85,
            "reasoning": "시장 가격 상승 추세"
        }
    )

@app.get("/api/v2/ai/trends")
async def get_market_trends(category: str = None, current_user: dict = Depends(verify_token)):
    """시장 트렌드 분석"""
    return APIResponse(
        success=True,
        message="시장 트렌드 분석 완료",
        data={
            "trend_direction": "up",
            "trend_strength": 0.7,
            "volatility": 0.3,
            "competitor_count": 5,
            "price_range": {"min": 30000, "max": 80000}
        }
    )

# 주문 관련 API
@app.post("/api/v2/orders")
async def create_order(order_data: dict, current_user: dict = Depends(verify_token)):
    """주문 생성"""
    return APIResponse(
        success=True,
        message="주문 생성 성공",
        data={
            "order_id": "order_12345",
            "status": "pending",
            "message": "주문이 성공적으로 생성되었습니다"
        }
    )

@app.get("/api/v2/orders")
async def get_orders(current_user: dict = Depends(verify_token)):
    """주문 목록 조회"""
    return APIResponse(
        success=True,
        message="주문 목록 조회 성공",
        data={
            "orders": [
                {
                    "id": "order_12345",
                    "status": "pending",
                    "total_amount": 50000,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "total": 1
        }
    )

# 공급사 관련 API
@app.get("/api/v2/suppliers")
async def get_suppliers(current_user: dict = Depends(verify_token)):
    """공급사 목록 조회"""
    return APIResponse(
        success=True,
        message="공급사 목록 조회 성공",
        data={
            "suppliers": [
                {
                    "id": "supplier_001",
                    "supplier_code": "ownerclan",
                    "account_name": "테스트 계정",
                    "is_active": True
                }
            ],
            "count": 1
        }
    )

@app.post("/api/v2/suppliers")
async def create_supplier(supplier_data: dict, current_user: dict = Depends(verify_token)):
    """공급사 계정 생성"""
    return APIResponse(
        success=True,
        message="공급사 계정 생성 성공",
        data={
            "supplier_code": supplier_data.get("supplier_code", "test_supplier")
        }
    )

# 분석 관련 API
@app.get("/api/v2/analytics/dashboard")
async def get_dashboard_analytics(current_user: dict = Depends(verify_token)):
    """대시보드 분석 데이터"""
    return APIResponse(
        success=True,
        message="대시보드 분석 데이터 조회 완료",
        data={
            "statistics": {
                "total_products": 1000,
                "total_orders": 50,
                "active_suppliers": 3,
                "platforms_monitored": 5
            },
            "trends": {
                "product_growth": 0.1,
                "order_growth": 0.2,
                "price_changes": 0.05
            }
        }
    )

# 배치 작업 API
@app.post("/api/v2/batch")
async def execute_batch_operation(batch_data: dict, current_user: dict = Depends(verify_token)):
    """배치 작업 실행"""
    return APIResponse(
        success=True,
        message="배치 작업이 백그라운드에서 시작되었습니다",
        data={
            "operation": batch_data.get("operation", "unknown"),
            "status": "started",
            "parameters": batch_data.get("parameters", {})
        }
    )

# 서버 시작
if __name__ == "__main__":
    logger.info("🚀 간단한 REST API 테스트 서버 시작")
    uvicorn.run(
        "simple_rest_api_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
