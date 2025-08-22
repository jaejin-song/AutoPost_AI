"""
뉴스 데이터 수집기

NewsAPI를 통한 키워드 기반 뉴스 수집
한국어 뉴스 우선, 최신순 정렬
"""

from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta
import requests

from ...utils.logger import get_logger
from ...utils.config import ConfigManager
from ...utils.retry import with_retry


logger = get_logger(__name__)


class NewsCollector:
    """뉴스 데이터 수집 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_key = config_manager.get_env_var('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
    
    @with_retry(max_attempts=3, delay=1.0)
    async def collect_news(self, trends_data: List[Dict], per_keyword: int = 5) -> List[Dict]:
        """트렌드 키워드 기반 뉴스 수집"""
        logger.info(f"뉴스 수집 시작: {len(trends_data)}개 키워드")
        
        all_news = []
        
        for trend in trends_data:
            keyword = trend.get('keyword')
            if not keyword:
                continue
            
            try:
                news_articles = await self._search_news_by_keyword(
                    keyword=keyword,
                    limit=per_keyword
                )
                
                # 트렌드 정보 추가
                for article in news_articles:
                    article['trend_rank'] = trend.get('rank')
                    article['trend_keyword'] = keyword
                
                all_news.extend(news_articles)
                
                # API 호출 제한 방지를 위한 딜레이
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 뉴스 수집 실패: {e}")
                continue
        
        logger.info(f"총 {len(all_news)}개 뉴스 기사 수집 완료")
        return all_news
    
    async def _search_news_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict]:
        """키워드로 뉴스 검색"""
        try:
            params = {
                'q': keyword,
                'language': 'ko',  # 한국어 우선
                'sortBy': 'publishedAt',  # 최신순
                'pageSize': min(limit, 20),  # 최대 20개
                'apiKey': self.api_key
            }
            
            # 한국 뉴스 소스 우선 검색
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            processed_articles = []
            for article in articles:
                processed_article = self._process_article(article, keyword)
                if processed_article:
                    processed_articles.append(processed_article)
            
            return processed_articles[:limit]
            
        except Exception as e:
            logger.error(f"뉴스 검색 실패 (키워드: {keyword}): {e}")
            return []
    
    def _process_article(self, article: Dict, keyword: str) -> Optional[Dict]:
        """뉴스 기사 데이터 처리"""
        try:
            # 필수 필드 확인
            if not article.get('title') or not article.get('description'):
                return None
            
            processed = {
                'title': article.get('title', '').strip(),
                'description': article.get('description', '').strip(),
                'content': article.get('content', '').strip(),
                'url': article.get('url'),
                'source': article.get('source', {}).get('name', ''),
                'author': article.get('author'),
                'published_at': article.get('publishedAt'),
                'url_to_image': article.get('urlToImage'),
                'keyword': keyword,
                'collected_at': datetime.now().isoformat(),
                'used_by_accounts': []  # 사용 추적을 위한 필드
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"기사 처리 실패: {e}")
            return None
    
    async def search_news_by_topic(self, topic: str, days: int = 7, limit: int = 10) -> List[Dict]:
        """주제별 뉴스 검색"""
        logger.info(f"주제별 뉴스 검색: {topic}")
        
        try:
            # 날짜 범위 설정
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            params = {
                'q': topic,
                'language': 'ko',
                'sortBy': 'relevancy',  # 관련성 순
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'pageSize': min(limit, 50),
                'apiKey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            processed_articles = []
            for article in articles:
                processed_article = self._process_article(article, topic)
                if processed_article:
                    processed_articles.append(processed_article)
            
            return processed_articles[:limit]
            
        except Exception as e:
            logger.error(f"주제별 뉴스 검색 실패 ({topic}): {e}")
            return []
    
    async def get_korean_headlines(self, limit: int = 20) -> List[Dict]:
        """한국 헤드라인 뉴스"""
        try:
            params = {
                'country': 'kr',
                'pageSize': min(limit, 50),
                'apiKey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            processed_articles = []
            for article in articles:
                processed_article = self._process_article(article, "korean_headlines")
                if processed_article:
                    processed_articles.append(processed_article)
            
            return processed_articles
            
        except Exception as e:
            logger.error(f"한국 헤드라인 수집 실패: {e}")
            return []