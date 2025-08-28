from trendspy import Trends

def get_trending_keywords(geo: str = "KR", count: int = 5):
    """
    trendspy를 이용한 Google Trends 실시간 인기 키워드 수집
    :param geo: 지역 코드 (예: 'KR' 한국, 'US' 미국)
    :param count: 가져올 키워드 개수
    :return: 키워드 리스트
    """
    try:
        tr = Trends()

        # 실시간 인기 키워드 조회
        trends = tr.trending_now(geo=geo)
        if not trends:
            print(f"[GoogleTrends] {geo} 지역 실시간 인기 검색어 없음")
            return []
        
        # print(dir(trends[0]))
        # print(trends[0].news)
        # print(trends[0].topic_names)
        # print(trends[0].topics)
        # print(trends[0].trend_keywords)
        # print(trends[0].volume)

        # 각 'title' 속성에서 상위 count개 추출
        keywords = [t.keyword for t in trends[:count]]
        print(f"[GoogleTrends] {geo} 인기 키워드 {len(keywords)}개 수집 완료")
        return keywords

    except Exception as e:
        print(f"[GoogleTrends] 오류 발생: {e}")
        return ["AI", "마케팅", "헬스케어"]  # fallback 더미 키워드
