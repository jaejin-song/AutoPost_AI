"""
워크플로우 관리 모듈

전체 AutoPost AI 프로세스를 조정하고 관리:
1. 데이터 수집 → 2. AI 처리 → 3. SNS 업로드
"""

from typing import Optional, Dict, List
import asyncio
from datetime import datetime

from ..data.collectors.trends_collector import TrendsCollector
from ..data.collectors.news_collector import NewsCollector
from ..data.storage.spreadsheet_manager import SpreadsheetManager
from ..ai.llm.ollama_client import OllamaClient
from ..ai.content.blog_generator import BlogGenerator
from ..ai.content.sns_generator import SnsGenerator
from ..automation.platforms.tistory_uploader import TistoryUploader
from ..automation.platforms.x_uploader import XUploader
from ..automation.platforms.threads_uploader import ThreadsUploader
from ..core.account_manager import AccountManager
from ..utils.logger import get_logger
from ..utils.config import ConfigManager


logger = get_logger(__name__)


class WorkflowManager:
    """워크플로우 관리 클래스"""
    
    def __init__(self, config_manager: ConfigManager, dry_run: bool = False):
        self.config_manager = config_manager
        self.dry_run = dry_run
        
        # 컴포넌트 초기화
        self._init_components()
    
    def _init_components(self):
        """필요한 컴포넌트들 초기화"""
        self.account_manager = AccountManager(self.config_manager)
        self.trends_collector = TrendsCollector(self.config_manager)
        self.news_collector = NewsCollector(self.config_manager)
        self.spreadsheet_manager = SpreadsheetManager(self.config_manager)
        
        # AI 컴포넌트
        self.ollama_client = OllamaClient(self.config_manager)
        self.blog_generator = BlogGenerator(self.ollama_client)
        self.sns_generator = SnsGenerator(self.ollama_client)
        
        # 업로더 컴포넌트
        self.uploaders = {
            'tistory': TistoryUploader(self.config_manager),
            'x': XUploader(self.config_manager),
            'threads': ThreadsUploader(self.config_manager)
        }
    
    async def run_daily_workflow(self, account_set: Optional[str] = None):
        """일별 워크플로우 실행"""
        logger.info("일별 워크플로우 시작")
        
        # 1. 데이터 수집 단계
        await self._collect_data()
        
        # 2. 계정 세트별 처리
        account_sets = self._get_target_account_sets(account_set)
        
        for account_set_name in account_sets:
            logger.info(f"계정 세트 처리 시작: {account_set_name}")
            await self._process_account_set(account_set_name)
    
    async def run_weekly_workflow(self, account_set: Optional[str] = None):
        """주별 워크플로우 실행"""
        logger.info("주별 워크플로우 시작")
        
        # 주별 트렌드 분석 및 계획 수립
        await self._analyze_weekly_trends()
        
        # 일별 워크플로우 실행
        await self.run_daily_workflow(account_set)
    
    async def _collect_data(self):
        """데이터 수집 단계"""
        logger.info("데이터 수집 시작")
        
        # 트렌드 데이터 수집
        trends_data = await self.trends_collector.collect_trending_keywords()
        
        # 뉴스 데이터 수집
        news_data = await self.news_collector.collect_news(trends_data)
        
        # 스프레드시트에 저장
        await self.spreadsheet_manager.save_data(trends_data, news_data)
        
        logger.info("데이터 수집 완료")
    
    async def _process_account_set(self, account_set_name: str):
        """특정 계정 세트 처리"""
        account_set = self.account_manager.get_account_set(account_set_name)
        
        # 1. 해당 주제에 맞는 뉴스 선별
        selected_news = await self._select_news_for_topic(account_set['topic'])
        
        # 2. 블로그 콘텐츠 생성
        blog_content = await self.blog_generator.generate_blog_post(
            selected_news, account_set['topic']
        )
        
        # 3. SNS 콘텐츠 생성
        sns_content = await self.sns_generator.generate_sns_posts(
            blog_content, account_set['topic']
        )
        
        # 4. 플랫폼별 업로드
        await self._upload_content(account_set, blog_content, sns_content)
    
    async def _select_news_for_topic(self, topic: str) -> List[Dict]:
        """주제에 맞는 뉴스 선별"""
        # 스프레드시트에서 미사용 뉴스 가져오기
        available_news = await self.spreadsheet_manager.get_unused_news(topic)
        
        # AI로 주제에 맞는 뉴스 선별
        selected_news = await self.ollama_client.select_relevant_news(
            available_news, topic
        )
        
        return selected_news
    
    async def _upload_content(self, account_set: Dict, blog_content: Dict, sns_content: Dict):
        """콘텐츠 업로드"""
        if self.dry_run:
            logger.info("DRY RUN 모드: 실제 업로드 건너뛰기")
            return
        
        # 계정별로 순차 업로드
        for account in account_set['accounts']:
            platform = account['platform']
            
            try:
                if platform in self.uploaders:
                    uploader = self.uploaders[platform]
                    
                    if platform == 'tistory':
                        await uploader.upload_blog_post(account, blog_content)
                    else:  # x, threads
                        await uploader.upload_sns_post(account, sns_content[platform])
                    
                    logger.info(f"{platform} 업로드 완료: {account['username']}")
                    
            except Exception as e:
                logger.error(f"{platform} 업로드 실패: {e}")
    
    async def _analyze_weekly_trends(self):
        """주별 트렌드 분석"""
        logger.info("주별 트렌드 분석 수행")
        # 주별 트렌드 분석 로직 구현 예정
        pass
    
    def _get_target_account_sets(self, account_set: Optional[str]) -> List[str]:
        """처리할 계정 세트 목록 반환"""
        if account_set:
            return [account_set] if account_set in self.account_manager.get_all_account_sets() else []
        
        return list(self.account_manager.get_all_account_sets().keys())