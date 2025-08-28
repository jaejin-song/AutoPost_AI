import requests
from config import load_env
from datetime import datetime, timedelta

# 환경 변수 로드
ENV = load_env()
NEWS_API_KEY = ENV.get("NEWS_API_KEY")

BASE_URL = "https://newsapi.org/v2"

# ----------------------------
# 뉴스 카테고리 상수 정의
# ----------------------------
class NewsCategory:
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    TECHNOLOGY = "technology"

def get_today_str():
    """
    오늘 날짜를 'YYYY-MM-DD' 포맷으로 반환
    """
    today = datetime.today()
    return today.strftime("%Y-%m-%d")

def get_yesterday_str():
    """
    어제 날짜를 'YYYY-MM-DD' 포맷으로 반환
    """
    yesterday = datetime.today() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def _extract_fields(articles):
    """
    NewsAPI articles에서 필요한 필드만 추출
    """
    result = []
    for a in articles:
        result.append({
            "title": a.get("title"),
            "url": a.get("url"),
            "content": a.get("content"),
            "publishedAt": a.get("publishedAt")
        })
    return result


def fetch_news_by_keywords(keywords, count=100, language="en"):
    """
    키워드 기반 뉴스 검색
    """
    if not NEWS_API_KEY:
        raise ValueError("❌ NEWS_API_KEY가 설정되지 않았습니다 (.env 확인 필요)")

    query = " OR ".join(keywords) if keywords else None
    params = {
        "q": query,
        "language": language,
        "pageSize": count,
        "sortBy": "relevancy",
        "from": get_yesterday_str(),
        "apiKey": NEWS_API_KEY,
    }

    resp = requests.get(f"{BASE_URL}/everything", params=params)
    data = resp.json()

    if resp.status_code != 200:
        print(f"[NewsAPI] 오류 발생: {data}")
        return []

    articles = data.get("articles", [])
    print(f"[NewsAPI] 키워드 {keywords} 관련 뉴스 {len(articles)}개 수집 완료")
    return _extract_fields(articles)


def fetch_latest_news(count=5, language="ko"):
    """
    최신 뉴스 가져오기 (키워드 X, publishedAt 기준)
    """
    if not NEWS_API_KEY:
        raise ValueError("❌ NEWS_API_KEY가 설정되지 않았습니다 (.env 확인 필요)")

    params = {
        "language": language,
        "pageSize": count,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
    }

    resp = requests.get(f"{BASE_URL}/everything", params=params)
    data = resp.json()

    if resp.status_code != 200:
        print(f"[NewsAPI] 오류 발생: {data}")
        return []

    articles = data.get("articles", [])
    print(f"[NewsAPI] 최신 뉴스 {len(articles)}개 수집 완료")
    return _extract_fields(articles)


def fetch_top_headlines(count=100, country="us", category=None):
    """
    많이 본 뉴스 / 주요 헤드라인 (국가별)
    """
    if not NEWS_API_KEY:
        raise ValueError("❌ NEWS_API_KEY가 설정되지 않았습니다 (.env 확인 필요)")

    params = {
        "country": country,
        "pageSize": count,
        "apiKey": NEWS_API_KEY,
    }
    
    if category:
        params["category"] = category

    resp = requests.get(f"{BASE_URL}/top-headlines", params=params)
    data = resp.json()

    if resp.status_code != 200:
        print(f"[NewsAPI] 오류 발생: {data}")
        return []

    articles = data.get("articles", [])
    print(f"[NewsAPI] {country.upper()} 주요 헤드라인 {len(articles)}개 수집 완료")
    return _extract_fields(articles)
