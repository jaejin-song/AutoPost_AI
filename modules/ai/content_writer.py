# 블로그 글 작성
import pprint
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
import re
import json
import os
from modules.storage.spreadsheet import _get_worksheet
from modules.utils import logger
from config import load_accounts
from pydantic import BaseModel
from modules.ai.prompts import get_prompt_template_for_set
from modules.ai.llm_providers import get_llm_provider
from modules.ai.pydantic_models import TopicSelection, BlogContentResponse

@dataclass
class Post:
    title: str
    content: str
    category: str
    tag: List[str]

# LLM Provider는 함수 호출시 동적으로 생성

def get_topics_from_spreadsheet(set_name: str) -> List[Dict]:
    """스프레드시트에서 사용되지 않은 주제 목록 가져오기"""
    try:
        worksheet = _get_worksheet(set_name=set_name)
        records = worksheet.get_all_records()
        
        # 아직 사용되지 않은 뉴스들만 필터링 (used 컬럼이 없거나 빈 값)
        unused_topics = []
        for record in records:
            if not record.get('used', ''):  # used 컬럼이 비어있으면 미사용
                unused_topics.append({
                    'title': record.get('title', ''),
                    'content': record.get('content', ''),
                    'url': record.get('url', ''),
                    'source': record.get('source', ''),
                    'subject': record.get('subject', ''),
                    'row_index': records.index(record) + 2  # 헤더 포함해서 +2
                })
        
        logger.log(f"스프레드시트에서 {len(unused_topics)}개의 미사용 주제를 가져왔습니다.")
        return unused_topics
        
    except Exception as e:
        logger.log(f"스프레드시트에서 주제를 가져오는 중 오류 발생: {e}")
        return []

def select_topics_with_ai(topics: List[Dict], set_name: str, count: int = 10) -> List[Dict]:
    """AI로 계정 세트에 맞는 주제 선정"""
    if not topics:
        return []
    
    # 계정 정보 로드
    accounts = load_accounts()
    account_info = accounts.get(set_name, {})
    account_topic = account_info.get('topic', '일반')
    account_description = account_info.get('description', '')
    
    # 주제 목록을 문자열로 변환
    topics_text = "\n".join([
        f"{i+1}. {topic['title']} - {topic['subject']}" 
        for i, topic in enumerate(topics[:50])  # 최대 50개까지만
    ])
    
    prompt = f"""
다음은 수집된 뉴스 주제 목록입니다:

{topics_text}

계정 정보:
- 주제: {account_topic}
- 설명: {account_description}

위 주제들 중에서 이 계정에 가장 적합한 {count}개를 선정해주세요.
선정 기준:
1. 계정 주제와의 연관성
2. 독자들의 관심도
3. 블로그 글로 작성하기 적합한 내용
4. 시의성과 유용성

⚠️ 주의사항:
- 유사한 주제는 중복해서 선택하지 말고 하나만 선택하세요.
- 반드시 정확히 {count}개의 주제 번호만 선택해야 합니다.
- {count}개보다 많거나 적게 선택하지 마세요.

반드시 아래 형식에 맞는 JSON만 반환하세요.  
추가적인 설명, 코드 블록, 텍스트는 절대 포함하지 마세요.  

반환 형식:
{{
  "selected_numbers": [정수 배열 (길이는 반드시 {count})],
  "reasoning": "간단한 설명 문자열"
}}

지금 바로 JSON만 출력하세요.
"""
    
    try:
        # LLM Provider 가져오기
        llm_provider = get_llm_provider(set_name)
        system_prompt = f'당신은 {account_topic} 블로그를 운영하는 파워 블로거입니다.'
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Ollama인 경우 구조화된 출력 사용, Claude인 경우 기존 방식 유지
        raw_response = llm_provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1024,
            temperature=0,
            format=TopicSelection  # Ollama에서 구조화된 출력 사용
        )
        
        if not raw_response:
            logger.log("LLM에서 응답을 받지 못했습니다")
            return random.sample(topics, min(count, len(topics)))
        
        # 구조화된 응답 파싱
        selected_topics = []
        logger.log(f"AI 응답 길이: {len(raw_response)} 문자")
        
        # 빈 응답 처리
        if not raw_response or not raw_response.strip():
            logger.log("AI에서 빈 응답을 받았습니다")
            return random.sample(topics, min(count, len(topics)))
        
        try:
            # Pydantic 모델로 파싱 시도 (구조화된 출력)
            # Ollama에서 정확한 JSON이 나오면 이 방법 사용
            try:
                topic_selection = TopicSelection.model_validate_json(raw_response)
                selected_numbers = topic_selection.selected_numbers
                logger.log(f"구조화된 파싱 성공: {selected_numbers}")
                
                for num in selected_numbers[:count]:
                    try:
                        index = int(num) - 1
                        if 0 <= index < len(topics):
                            selected_topics.append(topics[index])
                    except (ValueError, IndexError):
                        logger.log(f"잘못된 인덱스: {num}")
                        continue
                        
            except Exception:
                # 구조화된 파싱 실패시 기존 JSON 방식으로 fallback
                logger.log("구조화된 파싱 실패, JSON 파싱으로 fallback")
                
                # JSON 코드 블록 마커 제거
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # JSON 추출 및 파싱
                json_data = json.loads(cleaned_response)
                if json_data:
                    selected_numbers = json_data.get('selected_numbers', [])
                    logger.log(f"JSON 파싱 성공: {selected_numbers}")
                    
                    for num in selected_numbers[:count]:
                        try:
                            index = int(num) - 1
                            if 0 <= index < len(topics):
                                selected_topics.append(topics[index])
                        except (ValueError, IndexError):
                            logger.log(f"잘못된 인덱스: {num}")
                            continue
                else:
                    raise json.JSONDecodeError("JSON 추출 실패", "", 0)
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.log(f"JSON 파싱 실패: {str(e)}")
            logger.log("Regex 방식으로 fallback")
            
            # 최후 수단으로 regex 방식
            selected_numbers = re.findall(r'\d+', raw_response)
            logger.log(f"Regex로 추출된 번호들: {selected_numbers}")
            
            for num_str in selected_numbers[:count]:
                try:
                    index = int(num_str) - 1
                    if 0 <= index < len(topics):
                        selected_topics.append(topics[index])
                except (ValueError, IndexError):
                    continue
        
        logger.log(f"AI가 {len(selected_topics)}개의 주제를 선정했습니다.")
        return selected_topics
        
    except Exception as e:
        logger.log(f"AI 주제 선정 중 오류 발생: {e}")
        # 오류 시 랜덤으로 선택
        return random.sample(topics, min(count, len(topics)))


def generate_blog_content(set_name:str, topic: Dict) -> Optional[Post]:
    """AI로 블로그 글 생성"""
    
    # 계정 정보 로드
    accounts = load_accounts()
    account_info = accounts.get(set_name, {})
    account_topic = account_info.get('topic', '일반')
    account_language = account_info.get('language', '한국어')
    account_category = account_info.get('category', [])
    
    # 프롬프트 템플릿 선택 및 생성
    prompt = get_prompt_template_for_set(set_name, topic, account_topic, account_language, account_category)
    
    try:
        # LLM Provider 가져오기
        llm_provider = get_llm_provider(set_name)
        system_prompt = f'당신은 {account_topic} 블로그를 운영하는 파워 블로거이자 SEO 최적화 전문가입니다.'
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Ollama인 경우 구조화된 출력 사용, Claude인 경우 기존 방식 유지
        raw_response = llm_provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0,
            format=BlogContentResponse  # Ollama에서 구조화된 출력 사용
        )
        
        if not raw_response:
            logger.log("LLM에서 응답을 받지 못했습니다")
            return None
        
        # 빈 응답 처리
        if not raw_response or not raw_response.strip():
            logger.log("AI에서 글 생성 실패 - 빈 응답")
            return None
            
        try:
            # Pydantic 모델로 파싱 시도 (구조화된 출력)
            try:
                blog_response = BlogContentResponse.model_validate_json(raw_response)
                title = blog_response.title
                blog_content = blog_response.content
                category = blog_response.category or ''
                tags = blog_response.tags or []
                
                logger.log(f"구조화된 파싱 성공 - 제목: {title}")
                logger.log(f"구조화된 파싱 성공 - 내용 길이: {len(blog_content)}")
                
            except Exception:
                # 구조화된 파싱 실패시 기존 JSON 방식으로 fallback
                logger.log("구조화된 파싱 실패, JSON 파싱으로 fallback")
                
                # JSON 코드 블록 마커 제거
                cleaned_response = raw_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # JSON 추출 및 파싱
                json_data = json.loads(cleaned_response)
                if json_data:
                    title = json_data.get('title', topic['title'])
                    blog_content = json_data.get('content', '')
                    category = json_data.get('category', '')
                    tags = json_data.get('tags', [])
                    
                    logger.log(f"JSON 파싱 성공 - 제목: {title}")
                    logger.log(f"JSON 파싱 성공 - 내용 길이: {len(blog_content)}")
                    
                else:
                    raise json.JSONDecodeError("JSON 추출 실패", "", 0)
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.log(f"JSON 파싱 실패: {str(e)}")
            logger.log("텍스트 방식으로 fallback 처리")
            
            # 최후 수단으로 텍스트 방식 fallback
            blog_content = raw_response
            lines = blog_content.strip().split('\n')
            title = lines[0].replace('#', '').strip() if lines else topic['title']
            category = ''
            tags = []
            
            logger.log(f"Fallback 처리 - 제목: {title}")
        
        return Post(
            title=title,
            content=blog_content,
            category=category,
            tag=tags
        )
        
    except Exception as e:
        logger.log(f"블로그 글 생성 중 오류 발생: {e}")
        return None 

def mark_topic_as_used(topic: Dict, set_name: str):
    """스프레드시트에서 해당 주제를 사용됨으로 표시"""
    try:
        worksheet = _get_worksheet(set_name)
        row_index = topic['row_index']
        
        # used 컬럼에 계정 세트명과 사용일시 기록
        from datetime import datetime
        used_info = f"{set_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # used 컬럼이 몇 번째인지 확인 (없으면 추가)
        headers = worksheet.row_values(1)
        if 'used' not in headers:
            headers.append('used')
            worksheet.update('1:1', [headers])
            used_col = len(headers)
        else:
            used_col = headers.index('used') + 1
        
        # 해당 행의 used 컬럼 업데이트
        worksheet.update_cell(row_index, used_col, used_info)
        logger.log(f"주제 '{topic['title']}'을 사용됨으로 표시했습니다.")
        
    except Exception as e:
        logger.log(f"주제 사용 표시 중 오류 발생: {e}")

def generate_blog_post(set_name: str, max_posts: int = 10) -> List[Post]:
    """계정 세트별로 블로그 글 생성"""
    
    # 스프레드시트에서 주제 목록 가져오기
    topics = get_topics_from_spreadsheet(set_name=set_name)
    if not topics:
        logger.log("사용 가능한 주제가 없습니다.")
        return []
    
    # AI로 주제로 사용할 항목 선정
    accounts = load_accounts()
    account_info = accounts.get(set_name, {})
    
    selected_topics = select_topics_with_ai(topics, set_name, max_posts)
    if not selected_topics:
        logger.log("선정된 주제가 없습니다.")
        return []
    
    posts: List[Post] = []
    
    # AI로 글 생성
    for topic in selected_topics:
        try:
            post = generate_blog_content(set_name, topic)
            if post:
                posts.append(post)
                # 스프레드시트에 사용됨 표시
                mark_topic_as_used(topic, set_name)
                logger.log(f"블로그 글 생성 완료: {post.title}")
            else:
                logger.log(f"글 생성 실패: {topic['title']}")
                
        except Exception as e:
            logger.log(f"글 생성 중 오류 발생: {e}")
            continue
    
    logger.log(f"{set_name} 세트용 블로그 글 {len(posts)}개 생성 완료")
    return posts
