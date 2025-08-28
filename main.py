from config import load_accounts
from modules.collect import google_trends, news_api
# from modules.collect.news_api import fetch_top_headlines, fetch_news_by_keywords, NewsCategory
from modules.storage import spreadsheet
from modules.ai import content_writer, post_writer
from modules.publisher import runner
from modules.utils import logger

import pprint

def main():
    logger.log("🚀 AutoPost AI 시작")

    account_sets = load_accounts()

    for set_name, account_set in account_sets.items():
        logger.log(f"▶ [{set_name}] 세트 실행")

        # 1. 데이터 수집
        # keywords = google_trends.get_trending_keywords()
        
        # news_list = news_api.fetch_news(keywords)
        # news_list = news_api.fetch_top_headlines(category=NewsCategory.BUSINESS)
        news_list = news_api.fetch_news_by_keywords(keywords=set_name)

        # 2. 스프레드 시트 저장
        spreadsheet.save_news(news_list)
        quit()

        # 3. 뉴스 선정 및 글 작성
        for news in news_list:
            blog_post = content_writer.generate_blog_post(news)
            sns_posts = post_writer.generate_sns_posts(blog_post)

            # 4. 계정 세트별 업로드
            runner.publish_all(account_set, blog_post, sns_posts)

    logger.log("✅ AutoPost AI 완료")

if __name__ == "__main__":
    main()
