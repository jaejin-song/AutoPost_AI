"""
Google Trends 데이터 수집기

한국 지역 기준 트렌딩 키워드 수집
"""

from typing import List, Dict
import asyncio
from datetime import datetime, timedelta

from pytrends.request import TrendReq
from ...utils.logger import get_logger
from ...utils.config import ConfigManager
from ...utils.retry import with_retry


logger = get_logger(__name__)


class TrendsCollector:
    """Google Trends 데이터 수집 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.pytrends = TrendReq(hl='ko-KR', tz=540)  # 한국 시간대
    
    @with_retry(max_attempts=3, delay=1.0)
    async def collect_trending_keywords(self, limit: int = 25) -> List[Dict]:
        """트렌딩 키워드 수집"""
        logger.info("Google Trends에서 트렌딩 키워드 수집 시작")
        
        try:
            # 실시간 검색어 가져오기 (한국)
            trending_searches = self.pytrends.trending_searches(pn='south_korea')
            
            keywords = []
            for idx, keyword in enumerate(trending_searches[0].head(limit)):
                keyword_data = {
                    'keyword': keyword,
                    'rank': idx + 1,
                    'collected_at': datetime.now().isoformat(),
                    'source': 'google_trends',
                    'region': 'KR'
                }
                keywords.append(keyword_data)
            
            logger.info(f"트렌딩 키워드 {len(keywords)}개 수집 완료")
            return keywords
            
        except Exception as e:
            logger.error(f"트렌딩 키워드 수집 실패: {e}")
            raise
    
    @with_retry(max_attempts=3, delay=1.0)
    async def get_keyword_interest(self, keywords: List[str], timeframe: str = 'today 7-d') -> Dict:
        """키워드별 관심도 추이 데이터"""
        logger.info(f"키워드 관심도 분석: {keywords}")
        
        try:
            # 최대 5개 키워드만 한 번에 처리 (Google Trends 제한)
            if len(keywords) > 5:
                keywords = keywords[:5]
            
            self.pytrends.build_payload(keywords, timeframe=timeframe, geo='KR')
            interest_over_time = self.pytrends.interest_over_time()
            
            if interest_over_time.empty:
                return {}
            
            # 데이터 변환
            result = {}
            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    result[keyword] = {
                        'interest_data': interest_over_time[keyword].to_list(),
                        'peak_interest': interest_over_time[keyword].max(),
                        'avg_interest': interest_over_time[keyword].mean()
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"키워드 관심도 분석 실패: {e}")
            return {}
    
    async def get_related_queries(self, keyword: str) -> Dict:
        """연관 검색어 수집"""
        try:
            self.pytrends.build_payload([keyword], timeframe='today 7-d', geo='KR')
            
            # 상승 연관 검색어와 인기 연관 검색어
            related_queries = self.pytrends.related_queries()
            
            result = {
                'rising': [],
                'top': []
            }
            
            if keyword in related_queries:
                keyword_queries = related_queries[keyword]
                
                # 상승 검색어
                if keyword_queries['rising'] is not None:
                    result['rising'] = keyword_queries['rising']['query'].head(10).to_list()
                
                # 인기 검색어
                if keyword_queries['top'] is not None:
                    result['top'] = keyword_queries['top']['query'].head(10).to_list()
            
            return result
            
        except Exception as e:
            logger.error(f"연관 검색어 수집 실패 ({keyword}): {e}")
            return {'rising': [], 'top': []}