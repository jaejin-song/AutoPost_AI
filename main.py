from config import load_accounts
from modules.collect import google_trends, news_api, rss, reddit
# from modules.collect.news_api import fetch_top_headlines, fetch_news_by_keywords, NewsCategory
from modules.storage import spreadsheet
from modules.ai import content_writer, post_writer
from modules.publisher import runner
from modules.utils import logger

import pprint

from modules.utils.helpers import save_posts_to_file

def main():
    logger.log("🚀 AutoPost AI 시작")

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
        
        # reddit_posts = reddit.fetch_reddit_posts(subreddits=account_set['subreddits'])

        # 2. 스프레드 시트 저장
        # spreadsheet.save_news(set_name, reddit_posts)

        # 3. 뉴스 선정 및 글 작성
        # blog_posts = content_writer.generate_blog_post(set_name, max_posts=3)
        # save_posts_to_file(blog_post)
        
        # 4. 계정 세트별 업로드
        dummy_post = content_writer.Post(
            title="주식 시장 간단 브리핑",
            content="오늘 코스피 지수는 소폭 상승 마감했습니다.",
            category="주식",
            tag=["코스피", "주식", "증시"],
            upload_hour=9
        )
        blog_posts = [dummy_post]

        runner.publish_all(account_set, blog_posts, sns_posts=[])

    logger.log("✅ AutoPost AI 완료")

if __name__ == "__main__":
    main()
