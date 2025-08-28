# RSS 피드로 개인 금융 뉴스 수집 (예: CNBC Personal Finance)
import feedparser

def fetch_news_by_rss():
    rss_url = "https://www.chosun.com/arc/outboundfeeds/rss/category/national/?outputType=xml"
    feed = feedparser.parse(rss_url)
    
    rss_titles = [entry.title for entry in feed.entries[:10]]
    
    return feed.entries[0]