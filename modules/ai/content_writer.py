# 블로그 글 작성
from typing import List, Dict, Optional
import ollama
from dataclasses import dataclass
import random
import re
from modules.storage.spreadsheet import _get_worksheet
from modules.utils import logger
from config import load_accounts

@dataclass
class Post:
    title: str
    content: str
    category: str
    tag: List[str]
    upload_hour: int # 예약 시간

model = 'gemma3:4b'

def get_topics_from_spreadsheet() -> List[Dict]:
    """스프레드시트에서 사용되지 않은 주제 목록 가져오기"""
    try:
        worksheet = _get_worksheet()
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

결과는 번호만 콤마로 구분해서 답해주세요. (예: 1,5,12,23,45)
"""
    
    try:
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'system',
                'content': f'당신은 {account_topic} 전문 콘텐츠 큐레이터입니다.'
            }, {
                'role': 'user',
                'content': prompt
            }],
            options={
                'temperature': 0.3,
                'top_p': 0.8,
                'num_ctx': 4096
            }
        )
        
        # 선정된 번호 파싱
        selected_numbers = re.findall(r'\d+', response.message.content)
        selected_topics = []
        
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

def generate_blog_content(topic: Dict, account_theme: str) -> Optional[Post]:
    """AI로 블로그 글 생성"""
    
    theme_context = {
        '마케팅': 'marketing and online business growth',
        '관계': 'relationships and personal connections', 
        '건강': 'health and wellness',
        '금융': 'personal finance and money management'
    }
    
    context = theme_context.get(account_theme, 'general interest')
    
    prompt = f"""
다음 뉴스를 바탕으로 블로그 글을 작성해주세요:

제목: {topic['title']}
내용: {topic['content'][:500]}...
출처: {topic['source']}
주제: {topic['subject']}

요구사항:
1. 주제: {context} 관련 관점에서 작성
2. 구조: 제목 → 서론 → 본론(2-3개 섹션) → 결론 → CTA
3. 길이: 1000-1500 단어
4. SEO 최적화: 키워드 자연스럽게 포함
5. 톤: 전문적이면서도 읽기 쉽게
6. CTA: 독자 참여 유도 및 다른 글 읽기 권유
7. 글은 HTML로 작성

추가 지침:
- 단순 뉴스 요약이 아닌 해설과 의견 포함
- 독자에게 질문을 던져 생각해볼 거리 제공
- 실용적인 팁이나 조언 포함
- 중복 표현 피하고 다양한 어휘 사용

한국어로 작성해주세요.
"""
    
    try:
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'system', 
                'content': f'당신은 {context} 전문 블로거입니다. 독자에게 가치 있는 인사이트를 제공하는 글을 작성합니다.'
            }, {
                'role': 'user',
                'content': prompt
            }],
            options={
                'temperature': 0.8,
                'top_p': 0.9,
                'top_k': 40,
                'repeat_penalty': 1.1,
                'num_ctx': 4096
            }
        )
        
        blog_content = response.message.content
        
        # 제목 추출 (첫 번째 줄 또는 # 헤더)
        lines = blog_content.strip().split('\n')
        title = lines[0].replace('#', '').strip() if lines else topic['title']
        
        # 태그 생성
        tags = generate_tags(title + " " + blog_content[:200], account_theme)
        
        # 업로드 시간 랜덤 설정 (9-18시)
        upload_hour = random.randint(9, 18)
        
        return Post(
            title=title,
            content=blog_content,
            category=account_theme,
            tag=tags,
            upload_hour=upload_hour
        )
        
    except Exception as e:
        logger.log(f"블로그 글 생성 중 오류 발생: {e}")
        return None

def generate_tags(content: str, theme: str) -> List[str]:
    """콘텐츠에서 관련 태그 생성"""
    
    theme_tags = {
        '마케팅': ['마케팅', '온라인비즈니스', 'SNS마케팅', '디지털마케팅', '브랜딩'],
        '관계': ['관계', '연애', '인간관계', '소통', '사랑'],
        '건강': ['건강', '웰빙', '운동', '영양', '라이프스타일'],
        '금융': ['재테크', '투자', '저축', '부동산', '경제']
    }
    
    base_tags = theme_tags.get(theme, ['일반', '정보', '팁'])
    
    # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용 가능)
    keywords = re.findall(r'[가-힣]{2,4}', content)
    keyword_freq = {}
    for word in keywords:
        keyword_freq[word] = keyword_freq.get(word, 0) + 1
    
    # 빈도순으로 정렬하여 상위 키워드 추출
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    extracted_tags = [word for word, _ in top_keywords]
    
    # 기본 태그와 추출된 태그 결합
    all_tags = base_tags + extracted_tags
    return list(set(all_tags))[:7]  # 중복 제거 후 최대 7개

def mark_topic_as_used(topic: Dict, set_name: str):
    """스프레드시트에서 해당 주제를 사용됨으로 표시"""
    try:
        worksheet = _get_worksheet()
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

def generate_blog_post(set_name: str, max_posts: int = 5) -> List[Post]:
    """계정 세트별로 블로그 글 생성"""
    
    # 스프레드시트에서 주제 목록 가져오기
    topics = get_topics_from_spreadsheet()
    if not topics:
        logger.log("사용 가능한 주제가 없습니다.")
        return []
    
    # AI로 주제로 사용할 항목 선정
    accounts = load_accounts()
    account_info = accounts.get(set_name, {})
    account_theme = account_info.get('topic', '일반')
    
    selected_topics = select_topics_with_ai(topics, set_name, max_posts)
    if not selected_topics:
        logger.log("선정된 주제가 없습니다.")
        return []
    
    posts: List[Post] = []
    
    # AI로 글 생성
    for topic in selected_topics:
        try:
            post = generate_blog_content(topic, account_theme)
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
