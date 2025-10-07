#!/usr/bin/env python3
"""
간단한 상품 관리 대시보드 HTML 생성
72,376개 정규화 상품 관리 인터페이스
"""

import asyncio
from datetime import datetime
from loguru import logger
from src.services.database_service import DatabaseService


async def create_dashboard():
    """대시보드 HTML 생성"""
    
    db = DatabaseService()
    
    logger.info("📊 대시보드 생성 시작...")
    
    # 공급사별 통계
    suppliers = [
        ('오너클랜', 'e458e4e2-cb03-4fc2-bff1-b05aaffde00f', 'ownerclan'),
        ('젠트레이드', '959ddf49-c25f-4ebb-a292-bc4e0f1cd28a', 'zentrade'),
        ('도매꾹', 'baa2ccd3-a328-4387-b307-6ae89aea331b', 'domaemae')
    ]
    
    stats_html = ""
    total_products = 0
    
    for name, supplier_id, code in suppliers:
        products = await db.select_data("normalized_products", {"supplier_id": supplier_id})
        count = len(products)
        total_products += count
        
        # 가격 통계
        if products:
            prices = [p.get('price', 0) for p in products if p.get('price')]
            avg_price = sum(prices) / len(prices) if prices else 0
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
        else:
            avg_price = min_price = max_price = 0
        
        stats_html += f"""
        <div class="supplier-card">
            <h3>{name}</h3>
            <div class="stat-row">
                <div class="stat">
                    <div class="stat-label">상품 수</div>
                    <div class="stat-value">{count:,}개</div>
                </div>
                <div class="stat">
                    <div class="stat-label">평균 가격</div>
                    <div class="stat-value">₩{avg_price:,.0f}</div>
                </div>
            </div>
            <div class="stat-row">
                <div class="stat">
                    <div class="stat-label">최저가</div>
                    <div class="stat-value">₩{min_price:,.0f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">최고가</div>
                    <div class="stat-value">₩{max_price:,.0f}</div>
                </div>
            </div>
        </div>
        """
    
    # 샘플 상품 리스트 (상위 50개)
    sample_products = await db.select_data("normalized_products", {}, limit=50)
    
    products_html = ""
    for idx, product in enumerate(sample_products, 1):
        products_html += f"""
        <tr>
            <td>{idx}</td>
            <td class="product-title">{product.get('title', 'N/A')[:60]}...</td>
            <td>{product.get('category', 'N/A')}</td>
            <td class="price">₩{product.get('price', 0):,.0f}</td>
            <td class="price">₩{product.get('cost_price', 0):,.0f}</td>
            <td><span class="badge {product.get('status', 'active')}">{product.get('status', 'N/A')}</span></td>
        </tr>
        """
    
    # HTML 생성
    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>드롭쉬핑 상품 관리 대시보드</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: #666;
            font-size: 14px;
        }}
        
        .total-banner {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .total-banner h2 {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        
        .total-banner p {{
            font-size: 18px;
            opacity: 0.9;
        }}
        
        .supplier-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .supplier-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .supplier-card h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 22px;
        }}
        
        .stat-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-label {{
            color: #999;
            font-size: 13px;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }}
        
        .products-section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .products-section h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #f8f9fa;
        }}
        
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            color: #333;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .product-title {{
            font-weight: 500;
        }}
        
        .price {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge.active {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.inactive {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏪 드롭쉬핑 상품 관리 대시보드</h1>
            <p>데이터베이스 중심 아키텍처 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="total-banner">
            <h2>{total_products:,}개</h2>
            <p>총 정규화 상품 (3개 공급사)</p>
        </div>
        
        <div class="supplier-grid">
            {stats_html}
        </div>
        
        <div class="products-section">
            <h2>📦 최근 상품 (상위 50개)</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">No.</th>
                        <th>상품명</th>
                        <th style="width: 150px;">카테고리</th>
                        <th style="width: 120px;">판매가</th>
                        <th style="width: 120px;">원가</th>
                        <th style="width: 80px;">상태</th>
                    </tr>
                </thead>
                <tbody>
                    {products_html}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Dropshipping Automation System v2.0 | REST API: http://localhost:8000/api/docs</p>
        </div>
    </div>
</body>
</html>
    """
    
    # 파일 저장
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info("✅ 대시보드 생성 완료: dashboard.html")
    logger.info(f"   총 상품: {total_products:,}개")
    logger.info(f"   공급사: {len(suppliers)}개")


if __name__ == "__main__":
    asyncio.run(create_dashboard())

