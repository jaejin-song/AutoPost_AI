"""
블로그 콘텐츠 생성기

뉴스 기반 블로그 포스트 생성:
- 뉴스 + 해설 + 의견 3단 구조
- SEO 최적화
- 주제별 톤앤매너
"""

from typing import Dict, List, Optional
import asyncio
from datetime import datetime

from ..llm.ollama_client import OllamaClient
from ...utils.logger import get_logger


logger = get_logger(__name__)


class BlogGenerator:
    """블로그 콘텐츠 생성 클래스"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        
        # 주제별 톤앤매너 설정
        self.topic_styles = {
            '마케팅': {
                'tone': '전문적이고 실무적',
                'keywords': ['마케팅전략', 'ROI', '브랜딩', '고객경험', '디지털마케팅'],
                'cta': '마케팅 성과를 높이고 싶다면'
            },
            '관계/연애': {
                'tone': '공감적이고 따뜻한',
                'keywords': ['소통', '신뢰', '감정', '관계개선', '사랑'],
                'cta': '건강한 관계를 위해'
            },
            '건강/웰빙': {
                'tone': '신뢰할 수 있고 정보적',
                'keywords': ['건강관리', '예방', '생활습관', '웰니스', '자가관리'],
                'cta': '건강한 삶을 위해'
            },
            '개인 금융': {
                'tone': '신중하고 분석적',
                'keywords': ['투자전략', '리스크관리', '재무계획', '자산관리', '경제트렌드'],
                'cta': '현명한 투자를 위해'
            }
        }
    
    async def generate_blog_post(self, selected_news: List[Dict], topic: str) -> Dict:
        """블로그 포스트 생성"""
        if not selected_news:
            raise ValueError("선택된 뉴스가 없습니다")
        
        logger.info(f"'{topic}' 주제 블로그 포스트 생성 시작")
        
        # 메인 뉴스 선택 (첫 번째 뉴스)
        main_news = selected_news[0]
        
        try:
            # 1. 제목 생성
            title = await self._generate_title(main_news, topic)
            
            # 2. 본문 생성 (3단 구조)
            content_sections = await self._generate_content_sections(selected_news, topic)
            
            # 3. SEO 메타 정보 생성
            seo_meta = await self._generate_seo_meta(title, content_sections, topic)
            
            # 4. 최종 블로그 포스트 구성
            blog_post = {
                'title': title,
                'content': self._format_blog_content(content_sections),
                'meta_description': seo_meta['description'],
                'keywords': seo_meta['keywords'],
                'tags': seo_meta['tags'],
                'category': topic,
                'created_at': datetime.now().isoformat(),
                'source_news': [news.get('url') for news in selected_news],
                'word_count': self._count_words(content_sections)
            }
            
            logger.info(f"블로그 포스트 생성 완료: {blog_post['word_count']}자")
            return blog_post
            
        except Exception as e:
            logger.error(f"블로그 포스트 생성 실패: {e}")
            raise
    
    async def _generate_title(self, news: Dict, topic: str) -> str:
        """SEO 친화적 제목 생성"""
        style = self.topic_styles.get(topic, {})
        
        system_prompt = f"""
        당신은 '{topic}' 분야의 SEO 전문 블로거입니다.
        {style.get('tone', '전문적인')} 톤으로 매력적이고 클릭하고 싶은 제목을 만들어주세요.
        
        제목 작성 규칙:
        1. 30-60자 길이
        2. 키워드 포함: {', '.join(style.get('keywords', []))}
        3. 감정을 자극하는 표현
        4. 구체적인 숫자나 혜택 언급
        5. 검색 최적화 고려
        """
        
        prompt = f"""
        다음 뉴스를 바탕으로 '{topic}' 블로그의 매력적인 제목을 만들어주세요:
        
        뉴스 제목: {news.get('title', '')}
        뉴스 내용: {news.get('description', '')}
        
        3개의 제목 후보를 만들고, 가장 좋은 것을 선택해주세요.
        
        응답 형식:
        [선택된 최고의 제목]
        """
        
        response = await self.ollama_client.generate_completion(prompt, system_prompt)
        return response.split('\n')[0].strip()
    
    async def _generate_content_sections(self, news_list: List[Dict], topic: str) -> Dict:
        """3단 구조 콘텐츠 생성: 뉴스 + 해설 + 의견"""
        style = self.topic_styles.get(topic, {})
        
        system_prompt = f"""
        당신은 '{topic}' 분야의 전문 블로거입니다.
        {style.get('tone', '전문적인')} 톤으로 독자들에게 가치있는 콘텐츠를 제공합니다.
        
        글쓰기 스타일:
        - 톤: {style.get('tone', '전문적')}
        - 핵심 키워드: {', '.join(style.get('keywords', []))}
        - 독자층: {topic} 분야에 관심있는 일반인들
        """
        
        # 각 섹션별로 생성
        sections = {}
        
        # 1단계: 뉴스 정리 및 요약
        sections['news_summary'] = await self._generate_news_summary(news_list, system_prompt)
        
        # 2단계: 전문가 해설
        sections['expert_analysis'] = await self._generate_expert_analysis(news_list, topic, system_prompt)
        
        # 3단계: 개인 의견 및 인사이트
        sections['personal_insight'] = await self._generate_personal_insight(news_list, topic, system_prompt)
        
        # 4단계: 결론 및 CTA
        sections['conclusion'] = await self._generate_conclusion(topic, style.get('cta', ''), system_prompt)
        
        return sections
    
    async def _generate_news_summary(self, news_list: List[Dict], system_prompt: str) -> str:
        """뉴스 요약 섹션"""
        news_content = ""
        for i, news in enumerate(news_list[:3], 1):
            news_content += f"{i}. {news.get('title', '')}\n{news.get('description', '')}\n\n"
        
        prompt = f"""
        다음 뉴스들을 종합하여 핵심 내용을 정리해주세요:
        
        {news_content}
        
        요구사항:
        - 객관적이고 정확한 정보 전달
        - 3-4개 문단으로 구성
        - 핵심 포인트 강조
        - 독자가 이해하기 쉬운 설명
        
        소제목: ## 📰 최근 동향
        """
        
        return await self.ollama_client.generate_completion(prompt, system_prompt)
    
    async def _generate_expert_analysis(self, news_list: List[Dict], topic: str, system_prompt: str) -> str:
        """전문가 분석 섹션"""
        prompt = f"""
        위 뉴스들을 '{topic}' 분야 전문가 관점에서 심층 분석해주세요:
        
        분석 포인트:
        1. 이 동향이 '{topic}' 분야에 미치는 영향
        2. 숨겨진 의미와 배경
        3. 관련 업계/개인에게 주는 시사점
        4. 향후 전망과 예측
        
        요구사항:
        - 전문적이지만 이해하기 쉬운 설명
        - 구체적인 예시나 데이터 활용
        - 4-5개 문단으로 구성
        
        소제목: ## 🔍 전문가 분석
        """
        
        return await self.ollama_client.generate_completion(prompt, system_prompt)
    
    async def _generate_personal_insight(self, news_list: List[Dict], topic: str, system_prompt: str) -> str:
        """개인적 인사이트 섹션"""
        prompt = f"""
        이 뉴스와 분석을 바탕으로 개인적인 견해와 독창적인 인사이트를 제공해주세요:
        
        포함 요소:
        1. 개인적인 경험이나 관찰
        2. 남들이 놓칠 수 있는 포인트
        3. 실무진/개인에게 주는 구체적인 조언
        4. 차별화된 시각과 해석
        
        요구사항:
        - "내 생각으로는...", "개인적으로..." 등의 표현 활용
        - 독창적이고 차별화된 관점
        - 3-4개 문단으로 구성
        - 실용적인 팁이나 제안 포함
        
        소제목: ## 💭 개인적 견해
        """
        
        return await self.ollama_client.generate_completion(prompt, system_prompt)
    
    async def _generate_conclusion(self, topic: str, cta: str, system_prompt: str) -> str:
        """결론 및 CTA 섹션"""
        prompt = f"""
        글을 마무리하는 결론 부분을 작성해주세요:
        
        포함 요소:
        1. 핵심 내용 요약
        2. 독자에게 주는 핵심 메시지
        3. 행동 제안이나 다음 단계
        4. 독자와의 소통 유도
        
        마무리 문구: "{cta}"를 자연스럽게 활용해주세요.
        
        요구사항:
        - 2-3개 문단으로 구성
        - 독자 참여 유도 (댓글, 공유 등)
        - 긍정적이고 동기부여하는 톤
        
        소제목: ## 🎯 마무리
        """
        
        return await self.ollama_client.generate_completion(prompt, system_prompt)
    
    async def _generate_seo_meta(self, title: str, content_sections: Dict, topic: str) -> Dict:
        """SEO 메타 정보 생성"""
        full_content = ' '.join(content_sections.values())
        style = self.topic_styles.get(topic, {})
        
        system_prompt = f"""
        당신은 SEO 전문가입니다. '{topic}' 분야의 블로그 포스트에 최적화된 메타 정보를 생성해주세요.
        """
        
        prompt = f"""
        다음 블로그 포스트의 SEO 메타 정보를 생성해주세요:
        
        제목: {title}
        내용 요약: {full_content[:500]}...
        
        생성할 정보:
        1. 메타 설명 (150-160자, 매력적이고 클릭 유도)
        2. SEO 키워드 (5-8개)
        3. 태그 (3-5개)
        
        응답 형식 (JSON):
        {{
            "description": "메타 설명",
            "keywords": ["키워드1", "키워드2", ...],
            "tags": ["태그1", "태그2", ...]
        }}
        """
        
        response = await self.ollama_client.generate_completion(prompt, system_prompt)
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "description": title[:150] + "...",
                "keywords": style.get('keywords', [])[:5],
                "tags": [topic]
            }
    
    def _format_blog_content(self, sections: Dict) -> str:
        """섹션들을 최종 블로그 형식으로 조합"""
        content = ""
        
        for section_name, section_content in sections.items():
            content += section_content + "\n\n"
        
        return content.strip()
    
    def _count_words(self, sections: Dict) -> int:
        """글자 수 계산 (한글 기준)"""
        full_content = ' '.join(sections.values())
        return len(full_content.replace(' ', '').replace('\n', ''))