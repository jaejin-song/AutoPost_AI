import praw
from typing import List
from config import load_env
from modules.models.article import Article

ENV = load_env()
CLIENT_ID = ENV.get('CLIENT_ID')
CLIENT_SECRET = ENV.get('CLIENT_SECRET')
USER_AGENT = ENV.get('USER_AGENT')

def fetch_reddit_posts(subreddits: List[str]):
    reddit = praw.Reddit(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        user_agent = USER_AGENT
    )
    
    reddit_posts: List[Article] = []
    
    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).top(time_filter="day", limit=50):
            title = submission.title              # 글 제목
            content = submission.selftext         # 글 본문 (텍스트)
            url = submission.url                  # 외부 링크가 있으면 URL
            if content and len(content) >= 1000:
                reddit_posts.append(Article(
                        title=title,
                        content=content,
                        url=url,
                        source="reddit",
                        subject=subreddit
                ))
                
    return reddit_posts
    

