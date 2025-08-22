"""
SNS 콘텐츠 생성기

블로그 글에서 플랫폼별 SNS 콘텐츠 생성:
- X(트위터): 짧고 자극적, 해시태그 활용
- Threads: 스토리텔링, 커뮤니티 대화형
- 블로그 유입을 위한 CTA 포함
"""

from typing import Dict, List, Optional
import asyncio

from ..llm.ollama_client import OllamaClient
from ...utils.logger import get_logger


logger = get_logger(__name__)


class SnsGenerator:
    """SNS 콘텐츠 생성 클래스"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        
        # 플랫폼별 스타일 설정
        self.platform_styles = {
            'x': {
                'max_length': 280,
                'tone': '짧고 자극적',
                'features': ['해시태그', '임팩트', '화제성'],
                'cta': '자세한 내용은 블로그에서 👉',
                'hashtag_count': '3-5개'
            },
            'threads': {
                'max_length': 500,
                'tone': '스토리텔링, 커뮤니티 대화형',
                'features': ['공감', '대화유도', '스토리'],
                'cta': '더 깊은 이야기는 블로그에서 확인하세요 ✨',
                'hashtag_count': '1-3개'
            }
        }
    
    async def generate_sns_posts(self, blog_content: Dict, topic: str) -> Dict:
        """블로그 기반 SNS 포스트 생성"""
        logger.info(f"'{topic}' 주제 SNS 콘텐츠 생성 시작")
        
        try:
            # 각 플랫폼별 콘텐츠 생성
            sns_posts = {}
            
            # X(트위터) 포스트 생성
            sns_posts['x'] = await self._generate_x_post(blog_content, topic)
            
            # Threads 포스트 생성
            sns_posts['threads'] = await self._generate_threads_post(blog_content, topic)
            
            logger.info("SNS 콘텐츠 생성 완료")
            return sns_posts
            
        except Exception as e:
            logger.error(f"SNS 콘텐츠 생성 실패: {e}")
            raise
    
    async def _generate_x_post(self, blog_content: Dict, topic: str) -> Dict:
        """X(트위터) 포스트 생성"""
        style = self.platform_styles['x']
        
        system_prompt = f"""
        당신은 X(트위터) 콘텐츠 전문가입니다.
        '{topic}' 주제의 {style['tone']} 톤으로 매력적인 트윗을 작성합니다.
        
        트위터 특성:
        - 최대 {style['max_length']}자
        - {', '.join(style['features'])} 중시
        - {style['hashtag_count']} 해시태그 활용
        - 빠른 확산을 위한 임팩트
        """
        
        blog_summary = blog_content.get('content', '')[:500]  # 처음 500자만 요약용
        
        prompt = f"""
        다음 블로그 글을 바탕으로 X(트위터) 포스트를 작성해주세요:
        
        블로그 제목: {blog_content.get('title', '')}
        내용 요약: {blog_summary}
        
        요구사항:
        1. {style['max_length']}자 이내
        2. 흥미를 끌고 클릭을 유도하는 문구
        3. 관련 해시태그 {style['hashtag_count']}
        4. 마지막에 CTA: "{style['cta']}"
        
        응답 형식:
        [트윗 내용]
        """
        
        x_content = await self.ollama_client.generate_completion(prompt, system_prompt)
        
        return {
            'platform': 'x',
            'content': x_content.strip(),
            'hashtags': self._extract_hashtags(x_content),
            'character_count': len(x_content.strip()),
            'estimated_reach': 'medium'  # 추후 분석 기능 추가 가능
        }
    
    async def _generate_threads_post(self, blog_content: Dict, topic: str) -> Dict:
        """Threads 포스트 생성"""
        style = self.platform_styles['threads']
        
        system_prompt = f"""
        당신은 Meta Threads 콘텐츠 전문가입니다.
        '{topic}' 주제의 {style['tone']} 톤으로 공감과 대화를 유도하는 포스트를 작성합니다.
        
        Threads 특성:
        - 최대 {style['max_length']}자
        - {', '.join(style['features'])} 중시
        - {style['hashtag_count']} 해시태그 활용
        - 커뮤니티와의 소통 중시
        """
        
        blog_summary = blog_content.get('content', '')[:600]  # Threads는 조금 더 길게
        
        prompt = f"""
        다음 블로그 글을 바탕으로 Meta Threads 포스트를 작성해주세요:
        
        블로그 제목: {blog_content.get('title', '')}
        내용 요약: {blog_summary}
        
        요구사항:
        1. {style['max_length']}자 이내
        2. 스토리텔링과 공감을 유도하는 문구
        3. 질문이나 의견을 묻는 대화 유도 요소
        4. 관련 해시태그 {style['hashtag_count']}
        5. 마지막에 CTA: "{style['cta']}"
        
        응답 형식:
        [Threads 포스트 내용]
        """
        
        threads_content = await self.ollama_client.generate_completion(prompt, system_prompt)
        
        return {
            'platform': 'threads',
            'content': threads_content.strip(),
            'hashtags': self._extract_hashtags(threads_content),
            'character_count': len(threads_content.strip()),
            'engagement_type': 'community_discussion'
        }
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """텍스트에서 해시태그 추출"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return [tag.strip() for tag in hashtags]
    
    async def generate_variation_posts(self, original_post: Dict, variation_count: int = 3) -> List[Dict]:
        """기존 포스트의 변형 버전들 생성"""
        platform = original_post.get('platform', 'x')
        original_content = original_post.get('content', '')
        
        system_prompt = f"""
        당신은 {platform} 콘텐츠 전문가입니다.
        기존 포스트를 바탕으로 다양한 변형 버전을 만들어주세요.
        각 버전은 다른 접근 방식과 표현을 사용하되, 핵심 메시지는 유지해야 합니다.
        """
        
        prompt = f"""
        다음 {platform} 포스트의 변형 버전 {variation_count}개를 만들어주세요:
        
        원본 포스트:
        {original_content}
        
        각 변형 버전은:
        1. 다른 문체나 접근 방식 사용
        2. 핵심 메시지는 동일하게 유지
        3. 플랫폼 특성에 맞는 길이와 스타일
        4. 서로 다른 감정이나 톤
        
        응답 형식:
        [변형 1]
        ---
        [변형 2]
        ---
        [변형 3]
        """
        
        variations_text = await self.ollama_client.generate_completion(prompt, system_prompt)
        
        # 변형 버전들 파싱
        variations = []
        for i, variation in enumerate(variations_text.split('---')):
            variation = variation.strip()
            if variation:
                variations.append({
                    'platform': platform,
                    'content': variation,
                    'variation_id': i + 1,
                    'hashtags': self._extract_hashtags(variation),
                    'character_count': len(variation)
                })
        
        return variations[:variation_count]
    
    async def optimize_for_engagement(self, post_content: Dict) -> Dict:
        """참여도 최적화를 위한 포스트 개선"""
        platform = post_content.get('platform', 'x')
        content = post_content.get('content', '')
        
        system_prompt = f"""
        당신은 {platform} 마케팅 전문가입니다.
        포스트의 참여도(좋아요, 댓글, 공유)를 높이기 위한 최적화를 수행해주세요.
        """
        
        prompt = f"""
        다음 {platform} 포스트를 참여도를 높이도록 개선해주세요:
        
        원본 포스트:
        {content}
        
        최적화 포인트:
        1. 감정적 연결 강화
        2. 행동 유도 문구(CTA) 개선
        3. 질문이나 토론 유도 요소 추가
        4. 트렌드 해시태그나 키워드 활용
        5. 긴급성이나 호기심 유발
        
        응답 형식:
        [최적화된 포스트 내용]
        """
        
        optimized_content = await self.ollama_client.generate_completion(prompt, system_prompt)
        
        return {
            **post_content,
            'content': optimized_content.strip(),
            'optimization_applied': True,
            'hashtags': self._extract_hashtags(optimized_content),
            'character_count': len(optimized_content.strip())
        }
    
    async def analyze_post_performance(self, posts: List[Dict]) -> Dict:
        """포스트 성과 예측 분석"""
        try:
            analysis_results = []
            
            for post in posts:
                # 간단한 성과 예측 로직
                score = self._calculate_engagement_score(post)
                
                analysis_results.append({
                    'platform': post.get('platform'),
                    'predicted_engagement': score,
                    'character_count': post.get('character_count', 0),
                    'hashtag_count': len(post.get('hashtags', [])),
                    'recommendations': self._get_improvement_recommendations(post, score)
                })
            
            return {
                'posts_analyzed': len(posts),
                'average_score': sum(r['predicted_engagement'] for r in analysis_results) / len(analysis_results),
                'detailed_analysis': analysis_results
            }
            
        except Exception as e:
            logger.error(f"포스트 성과 분석 실패: {e}")
            return {'error': str(e)}
    
    def _calculate_engagement_score(self, post: Dict) -> float:
        """참여도 점수 계산 (0-10)"""
        score = 5.0  # 기본 점수
        
        content = post.get('content', '')
        hashtags = post.get('hashtags', [])
        platform = post.get('platform', 'x')
        
        # 해시태그 점수
        if hashtags:
            score += min(len(hashtags) * 0.3, 1.0)
        
        # 길이 점수 (플랫폼별 최적 길이)
        char_count = len(content)
        if platform == 'x':
            optimal_range = (100, 200)
        else:  # threads
            optimal_range = (150, 350)
        
        if optimal_range[0] <= char_count <= optimal_range[1]:
            score += 1.0
        
        # 질문 포함 점수
        if '?' in content:
            score += 0.5
        
        # 이모지 사용 점수
        emoji_count = len([c for c in content if ord(c) > 127])  # 간단한 이모지 감지
        if emoji_count > 0:
            score += min(emoji_count * 0.2, 0.8)
        
        return min(score, 10.0)
    
    def _get_improvement_recommendations(self, post: Dict, score: float) -> List[str]:
        """개선 추천사항"""
        recommendations = []
        
        if score < 6.0:
            recommendations.append("해시태그 추가로 도달 범위 확대")
        if '?' not in post.get('content', ''):
            recommendations.append("질문 추가로 상호작용 유도")
        if len(post.get('hashtags', [])) < 2:
            recommendations.append("관련 해시태그 2-3개 추가")
        if score < 5.0:
            recommendations.append("감정적 어필을 강화하는 표현 사용")
        
        return recommendations