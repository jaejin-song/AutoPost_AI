"""
Google Spreadsheet 저장소 관리자

수집된 트렌드/뉴스 데이터를 구글 스프레드시트에 저장하고
계정별 사용 추적을 관리
"""

from typing import List, Dict, Optional
import asyncio
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from ...utils.logger import get_logger
from ...utils.config import ConfigManager
from ...utils.retry import with_retry


logger = get_logger(__name__)


class SpreadsheetManager:
    """Google Spreadsheet 관리 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.spreadsheet_id = config_manager.get_env_var('GOOGLE_SHEETS_ID')
        self.client = self._init_client()
        self.spreadsheet = None
    
    def _init_client(self) -> gspread.Client:
        """Google Sheets 클라이언트 초기화"""
        try:
            service_account_file = self.config_manager.get_service_account_file()
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
            creds = Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            
            client = gspread.authorize(creds)
            logger.info("Google Sheets 클라이언트 초기화 완료")
            return client
            
        except Exception as e:
            logger.error(f"Google Sheets 클라이언트 초기화 실패: {e}")
            raise
    
    def _get_spreadsheet(self):
        """스프레드시트 객체 가져오기"""
        if not self.spreadsheet:
            try:
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                logger.info(f"스프레드시트 연결 완료: {self.spreadsheet.title}")
            except Exception as e:
                logger.error(f"스프레드시트 연결 실패: {e}")
                raise
        
        return self.spreadsheet
    
    @with_retry(max_attempts=3, delay=1.0)
    async def save_data(self, trends_data: List[Dict], news_data: List[Dict]):
        """트렌드와 뉴스 데이터 저장"""
        logger.info("스프레드시트에 데이터 저장 시작")
        
        spreadsheet = self._get_spreadsheet()
        
        # 트렌드 데이터 저장
        await self._save_trends_data(spreadsheet, trends_data)
        
        # 뉴스 데이터 저장
        await self._save_news_data(spreadsheet, news_data)
        
        logger.info("데이터 저장 완료")
    
    async def _save_trends_data(self, spreadsheet, trends_data: List[Dict]):
        """트렌드 데이터 시트에 저장"""
        try:
            # 트렌드 시트 가져오기 또는 생성
            try:
                worksheet = spreadsheet.worksheet('trends')
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title='trends', rows=1000, cols=10)
                # 헤더 추가
                headers = ['Date', 'Keyword', 'Rank', 'Source', 'Region', 'Collected_At']
                worksheet.append_row(headers)
            
            # 데이터 행 준비
            rows = []
            for trend in trends_data:
                row = [
                    datetime.now().strftime('%Y-%m-%d'),
                    trend.get('keyword', ''),
                    trend.get('rank', ''),
                    trend.get('source', ''),
                    trend.get('region', ''),
                    trend.get('collected_at', '')
                ]
                rows.append(row)
            
            # 배치로 데이터 추가
            if rows:
                worksheet.append_rows(rows)
                logger.info(f"트렌드 데이터 {len(rows)}개 행 저장")
                
        except Exception as e:
            logger.error(f"트렌드 데이터 저장 실패: {e}")
            raise
    
    async def _save_news_data(self, spreadsheet, news_data: List[Dict]):
        """뉴스 데이터 시트에 저장"""
        try:
            # 뉴스 시트 가져오기 또는 생성
            try:
                worksheet = spreadsheet.worksheet('news')
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title='news', rows=5000, cols=15)
                # 헤더 추가
                headers = [
                    'Date', 'Title', 'Description', 'URL', 'Source', 
                    'Author', 'Published_At', 'Keyword', 'Trend_Rank',
                    'Collected_At', 'Used_By_Accounts', 'Usage_Count'
                ]
                worksheet.append_row(headers)
            
            # 데이터 행 준비
            rows = []
            for news in news_data:
                row = [
                    datetime.now().strftime('%Y-%m-%d'),
                    news.get('title', ''),
                    news.get('description', ''),
                    news.get('url', ''),
                    news.get('source', ''),
                    news.get('author', ''),
                    news.get('published_at', ''),
                    news.get('keyword', ''),
                    news.get('trend_rank', ''),
                    news.get('collected_at', ''),
                    ','.join(news.get('used_by_accounts', [])),
                    len(news.get('used_by_accounts', []))
                ]
                rows.append(row)
            
            # 배치로 데이터 추가
            if rows:
                worksheet.append_rows(rows)
                logger.info(f"뉴스 데이터 {len(rows)}개 행 저장")
                
        except Exception as e:
            logger.error(f"뉴스 데이터 저장 실패: {e}")
            raise
    
    async def get_unused_news(self, topic: str, limit: int = 50) -> List[Dict]:
        """특정 주제의 미사용 뉴스 가져오기"""
        try:
            spreadsheet = self._get_spreadsheet()
            worksheet = spreadsheet.worksheet('news')
            
            # 모든 뉴스 데이터 가져오기
            all_records = worksheet.get_all_records()
            
            # 미사용 뉴스 필터링 (주제별)
            unused_news = []
            for record in all_records:
                # 사용되지 않았고 주제와 관련된 뉴스
                if (not record.get('Used_By_Accounts') and 
                    self._is_topic_relevant(record, topic)):
                    
                    unused_news.append(record)
                    
                    if len(unused_news) >= limit:
                        break
            
            logger.info(f"주제 '{topic}'의 미사용 뉴스 {len(unused_news)}개 반환")
            return unused_news
            
        except Exception as e:
            logger.error(f"미사용 뉴스 조회 실패: {e}")
            return []
    
    def _is_topic_relevant(self, news_record: Dict, topic: str) -> bool:
        """뉴스가 주제와 관련있는지 판단"""
        # 간단한 키워드 매칭 (추후 AI로 개선 가능)
        topic_keywords = {
            '마케팅': ['마케팅', '광고', '브랜딩', '소셜미디어', '디지털', '온라인', '비즈니스'],
            '관계/연애': ['연애', '결혼', '관계', '데이트', '커플', '사랑', '이별'],
            '건강/웰빙': ['건강', '운동', '다이어트', '영양', '웰빙', '의학', '병원'],
            '개인 금융': ['투자', '주식', '부동산', '금융', '경제', '재테크', '저축']
        }
        
        keywords = topic_keywords.get(topic, [])
        title = news_record.get('Title', '').lower()
        description = news_record.get('Description', '').lower()
        
        for keyword in keywords:
            if keyword in title or keyword in description:
                return True
        
        return False
    
    async def mark_news_as_used(self, news_url: str, account_set: str):
        """뉴스를 특정 계정 세트에서 사용했다고 표시"""
        try:
            spreadsheet = self._get_spreadsheet()
            worksheet = spreadsheet.worksheet('news')
            
            # URL로 해당 뉴스 행 찾기
            url_column = worksheet.col_values(4)  # URL은 4번째 컬럼
            
            for idx, url in enumerate(url_column[1:], start=2):  # 헤더 제외
                if url == news_url:
                    # 사용 계정 목록 업데이트
                    current_used = worksheet.cell(idx, 11).value or ''  # Used_By_Accounts 컬럼
                    used_accounts = current_used.split(',') if current_used else []
                    
                    if account_set not in used_accounts:
                        used_accounts.append(account_set)
                        
                        # 업데이트
                        new_used_accounts = ','.join(filter(None, used_accounts))
                        worksheet.update_cell(idx, 11, new_used_accounts)
                        worksheet.update_cell(idx, 12, len(used_accounts))  # Usage_Count
                        
                        logger.info(f"뉴스 사용 표시 완료: {account_set}")
                    break
                    
        except Exception as e:
            logger.error(f"뉴스 사용 표시 실패: {e}")
    
    async def get_usage_statistics(self) -> Dict:
        """사용 통계 조회"""
        try:
            spreadsheet = self._get_spreadsheet()
            
            # 트렌드 통계
            trends_worksheet = spreadsheet.worksheet('trends')
            trends_count = len(trends_worksheet.get_all_records())
            
            # 뉴스 통계
            news_worksheet = spreadsheet.worksheet('news')
            all_news = news_worksheet.get_all_records()
            news_count = len(all_news)
            used_news_count = sum(1 for news in all_news if news.get('Used_By_Accounts'))
            
            stats = {
                'total_trends': trends_count,
                'total_news': news_count,
                'used_news': used_news_count,
                'unused_news': news_count - used_news_count,
                'usage_rate': (used_news_count / news_count * 100) if news_count > 0 else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"사용 통계 조회 실패: {e}")
            return {}