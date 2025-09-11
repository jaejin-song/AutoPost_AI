from config import load_accounts
from modules.collect import google_trends, news_api, rss, reddit
# from modules.collect.news_api import fetch_top_headlines, fetch_news_by_keywords, NewsCategory
from modules.storage import spreadsheet
from modules.ai import content_writer, post_writer
from modules.publisher import runner
from modules.utils import logger

import pprint

from modules.utils.helpers import save_posts_to_file

dummy_content = """# 알리바바, 중국 AI 시장 판도 뒤흔들다

최근 알리바바가 자체 개발한 AI 칩을 공개하며 중국 AI 시장의 새로운 주자로 떠올랐습니다. 기존 Nvidia의 H20 칩을 대체할 수 있는 이 칩은 중국 기업들이 미국 제재로 인해 Nvidia 칩의 접근성이 떨어지는 상황에서, 중국 시장 점유율 확보를 위한 전략적 움직임으로 해석됩니다. 특히 알리바바의 이번 행보는 단순한 기술 개발을 넘어, 중국 정부의 ‘기술 자립’ 정책을 뒷받침하는 중요한 사례로 평가받고 있습니다.

## H20 칩, 중국 시장의 ‘블랙박스’

Nvidia의 H20 칩은 미국 정부의 수출 규제에 따라 중국 시장에 판매가 제한되던 ‘블랙박스’와 같은 존재였습니다. 미국 정부는 H20 칩의 성능과 기술이 중국 군사 기술 개발에 활용될 수 있다는 우려를 이유로 수출을 제한했습니다. 하지만 알리바바는 이러한 상황을 기회로 삼아 자체 AI 칩 개발에 박차를 가했습니다.
"""

# 그날의 가장 베스트 글을 보여주기 때문에 최대한 늦은 시간에 실행하는게 좋음.

def main():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    logger.log(f"🚀 AutoPost AI 시작 ({today})")

    account_sets = load_accounts()

    for set_name, account_set in account_sets.items():
        logger.log(f"▶ [{set_name}] 세트 실행")

        # 1. 데이터 수집
        # keywords = google_trends.get_trending_keywords()
        
        # news_list = news_api.fetch_news(keywords)
        # news_list = news_api.fetch_top_headlines(category=NewsCategory.BUSINESS)
        # news_list = news_api.fetch_news_by_keywords(keywords=set_name)
        
        # rss_news = rss.fetch_news_by_rss()
        # pprint.pprint(rss_news)
        
        reddit_posts = reddit.fetch_reddit_posts(subreddits=account_set['subreddits'])

        # # 2. 스프레드 시트 저장
        spreadsheet.save_news(set_name, reddit_posts)

        # # 3. 뉴스 선정 및 글 작성
        blog_posts = content_writer.generate_blog_post(set_name, max_posts=5)
        
        # from modules.ai.content_writer import Post
        # blog_posts = [
        #     Post(
        #         title="test",
        #         content=dummy_content,
        #         category="재테크",
        #         tag=[],
        #         upload_hour=1
        #     )
        # ]
        
        # 4. 계정 세트별 업로드
        runner.publish_all(account_set, blog_posts, set_name, sns_posts=[])
        
        # 5. 스프레드 시트 초기화
        spreadsheet.clear_worksheet(set_name)

    logger.log("✅ AutoPost AI 완료")

if __name__ == "__main__":
    main()
