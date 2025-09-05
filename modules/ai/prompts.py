# 블로그 글 작성용 프롬프트 템플릿 모듈
from typing import Dict, List
from config import load_accounts


# claude
def get_default_prompt_template(topic: Dict, account_topic: str, account_language: str, account_category: list) -> str:
    """기본 프롬프트 템플릿"""
    return f"""
아래에 제공된 정보를 바탕으로 블로그용 글을 작성해줘.  

입력 데이터:
제목: {topic['title']}
내용: {topic['content']}
출처: {topic['source']}

요구 사항:
1. "content"는 반드시 3000~4000자 사이의 분량으로 작성해.
2. 글의 톤은 사람이 쓴 것처럼 자연스럽게 작성하고, 지나치게 기계적이거나 번역투처럼 보이지 않게 해.
3. SEO 최적화를 고려해서 제목 및 본문에 핵심 키워드를 적절히 포함하되, 남용하지 말고 문맥에 자연스럽게 녹여라.
4. 본문은 HTML 태그를 활용해 구성하되, **h3/h4 소제목**, **굵은 글씨(strong)**, **목록(ul/li)**, **링크(a)** 등을 적절히 배치해 가독성과 검색 최적화를 동시에 달성해라.
5. 내용 속에는 실제 독자에게 도움이 될 만한 팁, 설명, 예시를 포함하고, 단순 요약이 아니라 풍부한 서술을 해라.
6. 제목은 사람들의 클릭을 유도할 수 있도록 지어줘.
7. 글의 마지막 부분에는 독자가 행동하도록 유도하는 문구(Call to Action)를 포함해라.
8. "category"에는 {account_category} 중 가장 적합한 단어 하나만 선택해 넣어라.
9. {account_language}로 작성해.

최종 출력은 아래와 같은 JSON 형식으로만 제공해.
{{
  "title": "블로그 글 제목",
  "content": "HTML 형식의 본문 전체",
  "category": {account_category} 중에서 가장 적합한 단어 1가지,
  "tags": 해당 글의 해시태그에 적합한 단어의 배열
}}
"""


def get_life_tips_prompt_template(topic: Dict, account_topic: str, account_language: str, account_category: list) -> str:
    """생활의빈틈 블로그 특화 프롬프트"""
    return f"""
아래에 제공된 레딧 글을 바탕으로 생활의 팁을 소개하는 글을 작성해줘.

입력 데이터:
제목: {topic['title']}
내용: {topic['content']}
출처: {topic['source']}

요구 사항:
1. 최종 출력은 JSON 형식으로 제공해.
2. JSON 구조는 아래와 같아:
{{
  "title": "마케팅 실무진을 위한 제목 (클릭을 유도하는 형태)",
  "content": "HTML 형식의 본문 전체 (h3, h4, p, strong, ul/li, a 태그 등을 적절히 활용)",
  "category": {account_category} 중에서 가장 적합한 단어 1가지,
  "tags": 마케팅 실무진이 검색할 만한 키워드 배열
}}
3. 커뮤니티에서 본 내용을 소개한다 정도로 출처를 얘기하고 "레딧"이라는 단어는 사용하지 말아줘.
4. 본문은 HTML 태그를 활용해 구성하되, **h3/h4 소제목**, **굵은 글씨(strong)**, **목록(ul/li)**, **링크(a)** 등을 적절히 배치해 가독성과 검색 최적화를 동시에 달성해라.
5. 제목은 사람들의 클릭을 유도할 수 있도록 지어줘.
6. 내용을 정리해서 소개하고 너의 생각을 덧붙여서 작성해줘.
7. 사람이 쓴 것처럼 자연스러운 글을 써줘.
8. {account_language}로 작성해.

출력은 반드시 JSON 형식만 출력해.
"""

def get_prompt_template_for_set(set_name: str, topic: Dict, account_topic: str, account_language: str, account_category: list) -> str:
    """계정 세트별로 적절한 프롬프트 템플릿 선택"""
    
    # 프롬프트 타입별 템플릿 선택
    prompt_templates = {
        'default': get_default_prompt_template,
        'finance': get_default_prompt_template,
        'jtaek': get_default_prompt_template,
        'life_tips': get_life_tips_prompt_template,
    }
    
    template_function = prompt_templates.get(set_name, get_default_prompt_template)
    return template_function(topic, account_topic, account_language, account_category)