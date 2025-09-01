from typing import List
import requests
from datetime import datetime, timedelta
import pytz
import random
from modules.ai.content_writer import Post

def category_to_number(category: str, set_name: str) -> int:
    """카테고리 이름을 WordPress 카테고리 ID로 변환"""
    from config import load_accounts
    
    accounts = load_accounts()
    account_set = accounts.get(set_name, {})
    category_map = account_set.get('wordpress_categories', {})
    
    return category_map.get(category, list(category_map.values())[0] if category_map else 100532)


def publish(blog_posts: List[Post], account, set_name: str):
    """WordPress.com REST API를 사용해 블로그 포스트 발행"""
    SITE_ID = account['SITE_ID']
    OAUTH2_TOKEN = account['OAUTH2_TOKEN']
    
    # WordPress.com Public API 엔드포인트
    api_url = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}/posts"
    
    for post in blog_posts:
        # 한국 시간대 기준으로 예약 시간 계산 (내일 랜덤 시간)
        tz = pytz.timezone("Asia/Seoul")
        tomorrow = datetime.now(tz) + timedelta(days=1)
        random_hour = random.randint(9, 21)  # 9시~21시 사이
        random_minute = random.randint(0, 59)  # 0~59분 사이
        future_time = tomorrow.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
        future_time_str = future_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # 발행할 글 데이터
        post_data = {
            "title": post.title,
            "content": post.content,
            "status": "future",
            "date": future_time_str,
            "categories": [category_to_number(post.category, set_name)],
        }
        
        # OAuth2 토큰을 사용한 API 요청
        headers = {
            "Authorization": f"Bearer {OAUTH2_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            api_url,
            json=post_data,
            headers=headers
        )
        
        if response.status_code == 201:
            post_url = response.json().get("link", "")
            print(f"✅ 글 발행 성공: {post.title}")
            print(f"   링크: {post_url}")
        else:
            print(f"❌ 글 발행 실패: {post.title}")
            print(f"   응답 코드: {response.status_code}")
            print(f"   오류 내용: {response.text}")
