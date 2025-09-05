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
        try:
            # top posts를 먼저 시도
            top_posts = list(reddit.subreddit(subreddit).top(time_filter="day", limit=50))
            
            # top posts가 없으면 hot posts로 fallback
            if len(top_posts) == 0:
                top_posts = list(reddit.subreddit(subreddit).hot(limit=50))
            
            for submission in top_posts:
                title = submission.title              # 글 제목
                content = submission.selftext         # 글 본문 (텍스트)
                url = submission.url                  # 외부 링크가 있으면 URL
                if content and len(content) >= 100:
                    reddit_posts.append(Article(
                            title=title,
                            content=content,
                            url=url,
                            source="reddit",
                            subject=subreddit
                    ))
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit}: {e}")
            continue
                
    return reddit_posts
    

