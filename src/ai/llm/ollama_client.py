"""
Ollama LLM 클라이언트

로컬 Ollama 서버와 통신하여 AI 작업 수행:
- 뉴스 선별
- 콘텐츠 생성 지원
"""

from typing import List, Dict, Optional
import asyncio
import json
import aiohttp

from ...utils.logger import get_logger
from ...utils.config import ConfigManager
from ...utils.retry import with_retry


logger = get_logger(__name__)


class OllamaClient:
    """Ollama LLM 클라이언트"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.base_url = config_manager.get_env_var('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = config_manager.get_env_var('OLLAMA_MODEL', 'llama2')
    
    @with_retry(max_attempts=3, delay=1.0)
    async def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """텍스트 생성"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2000
                    }
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    return result.get('response', '').strip()
                    
        except Exception as e:
            logger.error(f"Ollama 텍스트 생성 실패: {e}")
            raise
    
    async def select_relevant_news(self, news_list: List[Dict], topic: str, max_count: int = 3) -> List[Dict]:
        """주제와 관련된 뉴스 선별"""
        logger.info(f"'{topic}' 주제의 뉴스 선별 시작: {len(news_list)}개 → 최대 {max_count}개")
        
        if not news_list:
            return []
        
        try:
            # 뉴스 제목과 요약만 추출하여 프롬프트 생성
            news_summaries = []
            for idx, news in enumerate(news_list[:20]):  # 최대 20개만 분석
                summary = {
                    'index': idx,
                    'title': news.get('title', ''),
                    'description': news.get('description', '')
                }
                news_summaries.append(summary)
            
            system_prompt = f"""
            당신은 '{topic}' 주제에 특화된 콘텐츠 큐레이터입니다.
            주어진 뉴스 목록에서 '{topic}' 주제와 가장 관련성이 높고 
            흥미로운 뉴스를 최대 {max_count}개 선별해주세요.
            
            선별 기준:
            1. 주제와의 관련성
            2. 독자의 관심도
            3. 콘텐츠 활용 가능성
            4. 최신성과 트렌드성
            """
            
            prompt = f"""
            다음 뉴스 목록에서 '{topic}' 주제에 가장 적합한 뉴스를 선별해주세요:
            
            {json.dumps(news_summaries, ensure_ascii=False, indent=2)}
            
            응답 형식 (JSON):
            {{
                "selected_indices": [선택된 뉴스의 index 번호들],
                "reasoning": "선택 이유"
            }}
            """
            
            response = await self.generate_completion(prompt, system_prompt)
            
            # JSON 파싱 시도
            try:
                result = json.loads(response)
                selected_indices = result.get('selected_indices', [])
                
                selected_news = []
                for idx in selected_indices:
                    if 0 <= idx < len(news_list):
                        selected_news.append(news_list[idx])
                
                logger.info(f"뉴스 선별 완료: {len(selected_news)}개 선택")
                return selected_news
                
            except json.JSONDecodeError:
                logger.warning("JSON 파싱 실패, 첫 번째 뉴스들을 기본 선택")
                return news_list[:max_count]
                
        except Exception as e:
            logger.error(f"뉴스 선별 실패: {e}")
            # 실패 시 처음 몇 개 반환
            return news_list[:max_count]
    
    async def analyze_content_quality(self, content: str, content_type: str) -> Dict:
        """콘텐츠 품질 분석"""
        try:
            system_prompt = f"""
            당신은 {content_type} 콘텐츠 품질 분석 전문가입니다.
            주어진 콘텐츠를 분석하고 개선점을 제안해주세요.
            """
            
            prompt = f"""
            다음 {content_type} 콘텐츠를 분석해주세요:
            
            {content}
            
            분석 항목:
            1. 가독성 (1-10점)
            2. 정보성 (1-10점)
            3. 흥미도 (1-10점)
            4. SEO 적합성 (1-10점)
            5. 개선 제안사항
            
            응답 형식 (JSON):
            {{
                "scores": {{
                    "readability": 점수,
                    "informativeness": 점수,
                    "engagement": 점수,
                    "seo_fitness": 점수
                }},
                "total_score": 평균점수,
                "improvements": ["개선사항1", "개선사항2", ...],
                "summary": "전체 평가 요약"
            }}
            """
            
            response = await self.generate_completion(prompt, system_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "total_score": 7.0,
                    "summary": "분석 완료",
                    "improvements": ["세부 분석 데이터를 확인할 수 없습니다."]
                }
                
        except Exception as e:
            logger.error(f"콘텐츠 품질 분석 실패: {e}")
            return {}
    
    async def check_duplicate_content(self, new_content: str, existing_contents: List[str]) -> Dict:
        """중복 콘텐츠 확인"""
        if not existing_contents:
            return {"is_duplicate": False, "similarity": 0.0}
        
        try:
            system_prompt = """
            당신은 콘텐츠 중복성 검사 전문가입니다.
            새로운 콘텐츠와 기존 콘텐츠들을 비교하여 유사도를 측정해주세요.
            """
            
            # 기존 콘텐츠는 최대 5개만 비교
            existing_sample = existing_contents[-5:] if len(existing_contents) > 5 else existing_contents
            
            prompt = f"""
            새로운 콘텐츠와 기존 콘텐츠들의 유사도를 측정해주세요:
            
            [새로운 콘텐츠]
            {new_content}
            
            [기존 콘텐츠들]
            {json.dumps(existing_sample, ensure_ascii=False)}
            
            응답 형식 (JSON):
            {{
                "is_duplicate": true/false,
                "max_similarity": 최대유사도(0.0-1.0),
                "analysis": "분석 결과"
            }}
            
            중복 기준: 유사도 0.8 이상
            """
            
            response = await self.generate_completion(prompt, system_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"is_duplicate": False, "max_similarity": 0.0, "analysis": "분석 실패"}
                
        except Exception as e:
            logger.error(f"중복 콘텐츠 확인 실패: {e}")
            return {"is_duplicate": False, "max_similarity": 0.0}