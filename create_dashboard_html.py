"""
고급 React 대시보드 컴포넌트
"""

import os
from pathlib import Path

# React 대시보드 컴포넌트 생성
dashboard_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dropshipping Dashboard</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background-color: #f8fafc;
            color: #1e293b;
        }
        .dashboard { 
            display: grid; 
            grid-template-columns: 250px 1fr; 
            min-height: 100vh; 
        }
        .sidebar { 
            background: #1e293b; 
            color: white; 
            padding: 20px; 
        }
        .sidebar h2 { 
            margin-bottom: 30px; 
            color: #3b82f6; 
        }
        .sidebar ul { 
            list-style: none; 
        }
        .sidebar li { 
            margin-bottom: 10px; 
        }
        .sidebar a { 
            color: #cbd5e1; 
            text-decoration: none; 
            padding: 8px 12px; 
            border-radius: 6px; 
            display: block; 
            transition: all 0.2s; 
        }
        .sidebar a:hover, .sidebar a.active { 
            background: #3b82f6; 
            color: white; 
        }
        .main-content { 
            padding: 30px; 
        }
        .header { 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 30px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .stat-card { 
            background: white; 
            padding: 24px; 
            border-radius: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            border-left: 4px solid #3b82f6; 
        }
        .stat-value { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #1e293b; 
            margin-bottom: 8px; 
        }
        .stat-label { 
            color: #64748b; 
            font-size: 0.9em; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
        }
        .stat-change { 
            font-size: 0.8em; 
            margin-top: 8px; 
        }
        .stat-change.positive { color: #10b981; }
        .stat-change.negative { color: #ef4444; }
        .chart-container { 
            background: white; 
            padding: 24px; 
            border-radius: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            margin-bottom: 30px; 
        }
        .chart-title { 
            font-size: 1.2em; 
            font-weight: 600; 
            margin-bottom: 20px; 
            color: #1e293b; 
        }
        .loading { 
            text-align: center; 
            padding: 60px; 
            color: #64748b; 
        }
        .error { 
            text-align: center; 
            padding: 60px; 
            color: #ef4444; 
        }
        .search-section { 
            background: white; 
            padding: 24px; 
            border-radius: 12px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            margin-bottom: 30px; 
        }
        .search-form { 
            display: flex; 
            gap: 12px; 
            margin-bottom: 20px; 
        }
        .search-input { 
            flex: 1; 
            padding: 12px; 
            border: 1px solid #d1d5db; 
            border-radius: 8px; 
            font-size: 14px; 
        }
        .search-button { 
            padding: 12px 24px; 
            background: #3b82f6; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 500; 
        }
        .search-button:hover { 
            background: #2563eb; 
        }
        .product-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
        }
        .product-card { 
            background: white; 
            border-radius: 12px; 
            overflow: hidden; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
            transition: transform 0.2s; 
        }
        .product-card:hover { 
            transform: translateY(-2px); 
        }
        .product-image { 
            width: 100%; 
            height: 200px; 
            background: #f1f5f9; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #64748b; 
        }
        .product-info { 
            padding: 16px; 
        }
        .product-title { 
            font-weight: 600; 
            margin-bottom: 8px; 
            color: #1e293b; 
        }
        .product-price { 
            font-size: 1.2em; 
            font-weight: bold; 
            color: #3b82f6; 
            margin-bottom: 4px; 
        }
        .product-seller { 
            color: #64748b; 
            font-size: 0.9em; 
        }
        .alert-banner { 
            background: #fef3c7; 
            border: 1px solid #f59e0b; 
            color: #92400e; 
            padding: 12px 16px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .refresh-button { 
            position: fixed; 
            bottom: 30px; 
            right: 30px; 
            width: 60px; 
            height: 60px; 
            background: #3b82f6; 
            color: white; 
            border: none; 
            border-radius: 50%; 
            cursor: pointer; 
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); 
            font-size: 24px; 
        }
        .refresh-button:hover { 
            background: #2563eb; 
        }
        @media (max-width: 768px) {
            .dashboard { 
                grid-template-columns: 1fr; 
            }
            .sidebar { 
                display: none; 
            }
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useCallback } = React;
        
        function Dashboard() {
            const [activeTab, setActiveTab] = useState('overview');
            const [stats, setStats] = useState(null);
            const [searchResults, setSearchResults] = useState(null);
            const [loading, setLoading] = useState(true);
            const [error, setError] = useState(null);
            const [searchKeyword, setSearchKeyword] = useState('');
            const [searchLoading, setSearchLoading] = useState(false);
            
            const fetchDashboardStats = useCallback(async () => {
                try {
                    const response = await fetch('/api/dashboard/stats');
                    if (!response.ok) throw new Error('Failed to fetch stats');
                    const data = await response.json();
                    setStats(data);
                    setError(null);
                } catch (err) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            }, []);
            
            useEffect(() => {
                fetchDashboardStats();
                const interval = setInterval(fetchDashboardStats, 30000); // 30초마다 새로고침
                return () => clearInterval(interval);
            }, [fetchDashboardStats]);
            
            const handleSearch = async () => {
                if (!searchKeyword.trim()) return;
                
                setSearchLoading(true);
                try {
                    const response = await fetch('/api/search/products', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            keyword: searchKeyword,
                            platform: 'all',
                            page: 1
                        })
                    });
                    
                    if (!response.ok) throw new Error('Search failed');
                    const data = await response.json();
                    setSearchResults(data);
                } catch (err) {
                    setError(err.message);
                } finally {
                    setSearchLoading(false);
                }
            };
            
            const renderOverview = () => (
                <div>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">{stats?.total_products?.toLocaleString() || 0}</div>
                            <div className="stat-label">총 상품 수</div>
                            <div className="stat-change positive">+12% 이번 주</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{stats?.total_price_changes?.toLocaleString() || 0}</div>
                            <div className="stat-label">가격 변동</div>
                            <div className="stat-change negative">-5% 이번 주</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{stats?.active_alerts || 0}</div>
                            <div className="stat-label">활성 알림</div>
                            <div className="stat-change positive">+3 오늘</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{Object.keys(stats?.platforms || {}).length}</div>
                            <div className="stat-label">모니터링 플랫폼</div>
                        </div>
                    </div>
                    
                    <div className="chart-container">
                        <div className="chart-title">플랫폼별 상품 분포</div>
                        <canvas id="platformChart" width="400" height="200"></canvas>
                    </div>
                    
                    <div className="chart-container">
                        <div className="chart-title">인기 키워드 TOP 10</div>
                        <canvas id="keywordChart" width="400" height="200"></canvas>
                    </div>
                </div>
            );
            
            const renderSearch = () => (
                <div>
                    <div className="search-section">
                        <div className="search-form">
                            <input
                                type="text"
                                className="search-input"
                                placeholder="검색할 키워드를 입력하세요..."
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <button 
                                className="search-button" 
                                onClick={handleSearch}
                                disabled={searchLoading}
                            >
                                {searchLoading ? '검색 중...' : '검색'}
                            </button>
                        </div>
                    </div>
                    
                    {searchResults && (
                        <div>
                            <h3>검색 결과: {searchResults.keyword}</h3>
                            <div className="product-grid">
                                {Object.entries(searchResults.results).map(([platform, products]) => 
                                    products.map((product, index) => (
                                        <div key={`${platform}-${index}`} className="product-card">
                                            <div className="product-image">
                                                {product.image_url ? (
                                                    <img src={product.image_url} alt={product.name} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                                                ) : (
                                                    '이미지 없음'
                                                )}
                                            </div>
                                            <div className="product-info">
                                                <div className="product-title">{product.name}</div>
                                                <div className="product-price">{product.price?.toLocaleString()}원</div>
                                                <div className="product-seller">{product.seller} ({platform})</div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>
            );
            
            if (loading) return <div className="loading">로딩 중...</div>;
            if (error) return <div className="error">오류: {error}</div>;
            
            return (
                <div className="dashboard">
                    <div className="sidebar">
                        <h2>📊 Dashboard</h2>
                        <ul>
                            <li><a href="#" className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>개요</a></li>
                            <li><a href="#" className={activeTab === 'search' ? 'active' : ''} onClick={() => setActiveTab('search')}>상품 검색</a></li>
                            <li><a href="#" className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>가격 분석</a></li>
                            <li><a href="#" className={activeTab === 'alerts' ? 'active' : ''} onClick={() => setActiveTab('alerts')}>알림</a></li>
                            <li><a href="#" className={activeTab === 'settings' ? 'active' : ''} onClick={() => setActiveTab('settings')}>설정</a></li>
                        </ul>
                    </div>
                    
                    <div className="main-content">
                        <div className="header">
                            <h1>🚀 Dropshipping Dashboard</h1>
                            <p>실시간 경쟁사 데이터 모니터링 및 분석</p>
                            <div style={{marginTop: '10px', fontSize: '0.9em', color: '#64748b'}}>
                                마지막 업데이트: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'N/A'}
                            </div>
                        </div>
                        
                        {activeTab === 'overview' && renderOverview()}
                        {activeTab === 'search' && renderSearch()}
                        {activeTab === 'analysis' && <div>가격 분석 기능 (개발 중)</div>}
                        {activeTab === 'alerts' && <div>알림 관리 기능 (개발 중)</div>}
                        {activeTab === 'settings' && <div>설정 기능 (개발 중)</div>}
                        
                        <button className="refresh-button" onClick={fetchDashboardStats} title="새로고침">
                            🔄
                        </button>
                    </div>
                </div>
            );
        }
        
        ReactDOM.render(<Dashboard />, document.getElementById('root'));
        
        // 차트 렌더링 함수
        function renderCharts(stats) {
            if (!stats) return;
            
            // 플랫폼 차트
            const platformCtx = document.getElementById('platformChart');
            if (platformCtx) {
                new Chart(platformCtx.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(stats.platforms),
                        datasets: [{
                            data: Object.values(stats.platforms),
                            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            // 키워드 차트
            const keywordCtx = document.getElementById('keywordChart');
            if (keywordCtx) {
                new Chart(keywordCtx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: Object.keys(stats.keywords),
                        datasets: [{
                            label: '상품 수',
                            data: Object.values(stats.keywords),
                            backgroundColor: '#3b82f6',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }
        }
        
        // 차트 렌더링을 위한 전역 함수
        window.renderCharts = renderCharts;
    </script>
</body>
</html>
"""

# HTML 파일로 저장
dashboard_path = Path("src/api/dashboard.html")
dashboard_path.write_text(dashboard_html, encoding="utf-8")
