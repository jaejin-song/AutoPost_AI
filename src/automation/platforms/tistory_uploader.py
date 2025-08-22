"""
티스토리 블로그 업로더

Playwright를 사용한 웹 자동화로 티스토리 블로그 포스팅
- 로그인
- 포스트 작성 및 발행
- SEO 설정
"""

from typing import Dict, Optional
import asyncio
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from ...utils.logger import get_logger
from ...utils.config import ConfigManager
from ...utils.retry import with_retry


logger = get_logger(__name__)


class TistoryUploader:
    """티스토리 업로더 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def upload_blog_post(self, account: Dict, blog_content: Dict) -> Dict:
        """블로그 포스트 업로드"""
        logger.info(f"티스토리 업로드 시작: {account.get('username')}")
        
        try:
            async with async_playwright() as p:
                # 브라우저 시작
                self.browser = await p.chromium.launch(headless=True)
                self.context = await self.browser.new_context()
                
                page = await self.context.new_page()
                
                # 로그인
                await self._login(page, account)
                
                # 글쓰기 페이지로 이동
                await page.goto(f"{account['blog_url']}/manage/entry/write")
                
                # 포스트 작성
                await self._write_post(page, blog_content)
                
                # 발행
                post_url = await self._publish_post(page)
                
                logger.info(f"티스토리 업로드 완료: {post_url}")
                return {
                    'success': True,
                    'post_url': post_url,
                    'published_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"티스토리 업로드 실패: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            if self.browser:
                await self.browser.close()
    
    async def _login(self, page: Page, account: Dict):
        """티스토리 로그인"""
        await page.goto('https://www.tistory.com/auth/login')
        
        # 로그인 폼 입력
        await page.fill('input[name="loginId"]', account['username'])
        await page.fill('input[name="password"]', account['password'])
        await page.click('button[type="submit"]')
        
        # 로그인 완료 대기
        await page.wait_for_url('**/manage/**', timeout=10000)
    
    async def _write_post(self, page: Page, blog_content: Dict):
        """포스트 작성"""
        # 제목 입력
        await page.fill('input[name="title"]', blog_content['title'])
        
        # 내용 입력 (HTML 에디터)
        await page.evaluate(
            '(content) => { editor.setHtml(content); }',
            blog_content['content']
        )
        
        # 카테고리 설정 (필요시)
        if blog_content.get('category'):
            await page.select_option('select[name="category"]', blog_content['category'])
        
        # 태그 입력
        if blog_content.get('tags'):
            tags_str = ', '.join(blog_content['tags'])
            await page.fill('input[name="tag"]', tags_str)
    
    async def _publish_post(self, page: Page) -> str:
        """포스트 발행"""
        # 발행 버튼 클릭
        await page.click('button:has-text("발행")')
        
        # 발행 완료 대기 및 URL 추출
        await page.wait_for_selector('.success-message', timeout=10000)
        
        # 발행된 포스트 URL 반환 (실제 구현 시 정확한 셀렉터 필요)
        current_url = page.url
        return current_url  # 임시 반환값