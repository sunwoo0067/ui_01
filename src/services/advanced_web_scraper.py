"""
고급 웹 스크래핑 우회 시스템
"""

import asyncio
import random
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import aiohttp
import json
from loguru import logger
from fake_useragent import UserAgent

from src.config.settings import settings
from src.utils.error_handler import ErrorHandler


class ProxyManager:
    """프록시 관리 클래스"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.failed_proxies = set()
        
    def add_proxy(self, proxy_url: str):
        """프록시 추가"""
        self.proxies.append(proxy_url)
        
    def get_next_proxy(self) -> Optional[str]:
        """다음 프록시 반환"""
        if not self.proxies:
            return None
            
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        if not available_proxies:
            # 모든 프록시가 실패한 경우 리셋
            self.failed_proxies.clear()
            available_proxies = self.proxies
            
        proxy = random.choice(available_proxies)
        return proxy
        
    def mark_proxy_failed(self, proxy_url: str):
        """프록시 실패 표시"""
        self.failed_proxies.add(proxy_url)


class UserAgentRotator:
    """User-Agent 로테이션 클래스"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
        ]
        
    def get_random_user_agent(self) -> str:
        """랜덤 User-Agent 반환"""
        try:
            # fake_useragent에서 랜덤 생성
            return self.ua.random
        except:
            # 실패 시 미리 정의된 목록에서 선택
            return random.choice(self.user_agents)


class RequestDelayManager:
    """요청 딜레이 관리 클래스"""
    
    def __init__(self):
        self.min_delay = 1.0  # 최소 딜레이 (초)
        self.max_delay = 5.0  # 최대 딜레이 (초)
        self.last_request_time = 0
        
    async def wait_if_needed(self):
        """필요시 딜레이 대기"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            await asyncio.sleep(wait_time)
            
        self.last_request_time = time.time()


class AdvancedWebScraper:
    """고급 웹 스크래핑 클래스"""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.ua_rotator = UserAgentRotator()
        self.delay_manager = RequestDelayManager()
        self.error_handler = ErrorHandler()
        
        # 세션 설정
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        
    async def make_request(self, 
                         url: str, 
                         method: str = 'GET',
                         headers: Optional[Dict[str, str]] = None,
                         params: Optional[Dict[str, Any]] = None,
                         data: Optional[Any] = None,
                         use_proxy: bool = True,
                         retry_count: int = 0) -> Optional[aiohttp.ClientResponse]:
        """
        고급 웹 요청 수행
        
        Args:
            url: 요청 URL
            method: HTTP 메서드
            headers: 헤더
            params: 쿼리 파라미터
            data: 요청 데이터
            use_proxy: 프록시 사용 여부
            retry_count: 재시도 횟수
            
        Returns:
            aiohttp.ClientResponse: 응답 객체
        """
        try:
            # 딜레이 대기
            await self.delay_manager.wait_if_needed()
            
            # 헤더 설정
            if headers is None:
                headers = {}
                
            headers.update({
                'User-Agent': self.ua_rotator.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            })
            
            # 프록시 설정
            proxy = None
            if use_proxy and self.proxy_manager.proxies:
                proxy = self.proxy_manager.get_next_proxy()
                
            # 커넥터 설정
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.session_timeout,
                headers=headers
            ) as session:
                
                # 요청 수행
                if method.upper() == 'GET':
                    async with session.get(url, params=params, proxy=proxy) as response:
                        if response.status == 200:
                            return response
                        elif response.status in [429, 503, 504]:  # Rate limit 또는 서버 오류
                            await self._handle_rate_limit(response, proxy)
                            if retry_count < self.max_retries:
                                return await self.make_request(
                                    url, method, headers, params, data, use_proxy, retry_count + 1
                                )
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            
                elif method.upper() == 'POST':
                    async with session.post(url, params=params, data=data, proxy=proxy) as response:
                        if response.status == 200:
                            return response
                        elif response.status in [429, 503, 504]:
                            await self._handle_rate_limit(response, proxy)
                            if retry_count < self.max_retries:
                                return await self.make_request(
                                    url, method, headers, params, data, use_proxy, retry_count + 1
                                )
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"요청 타임아웃: {url}")
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"클라이언트 오류: {url} - {e}")
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': '고급 웹 스크래핑 요청 실패',
                'url': url,
                'retry_count': retry_count
            })
            return None

    async def _handle_rate_limit(self, response: aiohttp.ClientResponse, proxy: Optional[str]):
        """Rate limit 처리"""
        try:
            # Retry-After 헤더 확인
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                logger.info(f"Rate limit 감지, {wait_time}초 대기")
                await asyncio.sleep(wait_time)
            else:
                # 기본 대기 시간
                wait_time = random.uniform(5, 15)
                logger.info(f"Rate limit 감지, {wait_time:.1f}초 대기")
                await asyncio.sleep(wait_time)
                
            # 프록시 실패 표시
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
                
        except Exception as e:
            logger.error(f"Rate limit 처리 중 오류: {e}")

    def add_proxy(self, proxy_url: str):
        """프록시 추가"""
        self.proxy_manager.add_proxy(proxy_url)
        
    def set_delay_range(self, min_delay: float, max_delay: float):
        """딜레이 범위 설정"""
        self.delay_manager.min_delay = min_delay
        self.delay_manager.max_delay = max_delay

    async def test_proxy(self, proxy_url: str) -> bool:
        """프록시 테스트"""
        try:
            test_url = "https://httpbin.org/ip"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"프록시 테스트 성공: {proxy_url} - IP: {data.get('origin')}")
                        return True
                    else:
                        logger.warning(f"프록시 테스트 실패: {proxy_url} - HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"프록시 테스트 중 오류: {proxy_url} - {e}")
            return False

    async def get_page_content(self, url: str, encoding: str = 'utf-8') -> Optional[str]:
        """페이지 내용 가져오기"""
        try:
            response = await self.make_request(url)
            if response:
                content = await response.text(encoding=encoding)
                return content
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': '페이지 내용 가져오기 실패',
                'url': url
            })
            return None

    async def get_json_data(self, url: str) -> Optional[Dict[str, Any]]:
        """JSON 데이터 가져오기"""
        try:
            response = await self.make_request(url)
            if response:
                data = await response.json()
                return data
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, {
                'operation': 'JSON 데이터 가져오기 실패',
                'url': url
            })
            return None


class ProxyScraper:
    """무료 프록시 수집 클래스"""
    
    def __init__(self):
        self.scraper = AdvancedWebScraper()
        
    async def get_free_proxies(self) -> List[str]:
        """무료 프록시 목록 수집"""
        proxies = []
        
        try:
            # Free Proxy List에서 프록시 수집
            proxy_urls = [
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            ]
            
            for url in proxy_urls:
                try:
                    content = await self.scraper.get_page_content(url)
                    if content:
                        proxy_list = content.strip().split('\n')
                        proxies.extend([f"http://{proxy.strip()}" for proxy in proxy_list if proxy.strip()])
                        logger.info(f"프록시 수집: {len(proxy_list)}개")
                except Exception as e:
                    logger.error(f"프록시 수집 실패: {url} - {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"프록시 수집 중 오류: {e}")
            
        return proxies

    async def validate_proxies(self, proxies: List[str]) -> List[str]:
        """프록시 유효성 검증"""
        valid_proxies = []
        
        tasks = []
        for proxy in proxies[:20]:  # 최대 20개만 테스트
            task = self.scraper.test_proxy(proxy)
            tasks.append((proxy, task))
            
        for proxy, task in tasks:
            try:
                is_valid = await task
                if is_valid:
                    valid_proxies.append(proxy)
            except Exception as e:
                logger.error(f"프록시 검증 실패: {proxy} - {e}")
                
        logger.info(f"유효한 프록시: {len(valid_proxies)}개")
        return valid_proxies


# 전역 인스턴스
advanced_scraper = AdvancedWebScraper()
proxy_scraper = ProxyScraper()
