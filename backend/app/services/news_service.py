"""新闻服务"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.news import GoldNews, SentimentType
import feedparser
from email.utils import parsedate_to_datetime


class NewsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_news(self, limit: int = 20, source: str = None, sentiment: str = None) -> List[GoldNews]:
        query = self.db.query(GoldNews)
        
        if source:
            query = query.filter(GoldNews.source == source)
        
        if sentiment:
            query = query.filter(GoldNews.sentiment == sentiment)
        
        return query.order_by(GoldNews.published_at.desc()).limit(limit).all()
    
    def get_news_by_id(self, news_id: int) -> Optional[GoldNews]:
        return self.db.query(GoldNews).filter(GoldNews.id == news_id).first()
    
    def get_sentiment_summary(self) -> Dict[str, int]:
        stats = self.db.query(
            GoldNews.sentiment,
            func.count(GoldNews.id)
        ).group_by(GoldNews.sentiment).all()
        
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            **{s[0].value: s[1] for s in stats}
        }
    
    def fetch_from_rss(self, rss_url: str, source: str, limit: int = 10) -> List[Dict]:
        try:
            feed = feedparser.parse(
                rss_url,
                request_headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            news_list = []
            for entry in feed.entries[:limit]:
                published_at = None
                published = entry.get('published') or entry.get('updated')
                if published:
                    try:
                        published_at = parsedate_to_datetime(published)
                    except Exception:
                        published_at = None

                summary = entry.get('summary', '')
                link = entry.get('link', '')
                news_list.append({
                    'title': entry.title,
                    'summary': summary,
                    'content': summary,
                    'link': link,
                    'url': link,
                    'published_at': published_at,
                    'source': source
                })
            
            return news_list
        except Exception as e:
            print(f"RSS获取失败 {source}: {e}")
            return []
    
    def fetch_all_rss_news(self) -> List[Dict]:
        all_news = []
        
        rss_sources = [
            ('https://news.kitco.com/rss/kitconewsfeed.xml', 'Kitco News'),
            ('https://kingworldnews.com/feed/', 'King World News'),
            ('https://www.mining.com/feed/', 'MINING.com'),
        ]

        for rss_url, source in rss_sources:
            try:
                news = self.fetch_from_rss(rss_url, source, limit=5)
                all_news.extend(news)
            except Exception as e:
                print(f"RSS获取失败 {source}: {e}")
        
        return all_news
    
    def save_news(self, news_data: Dict):
        try:
            existing = self.db.query(GoldNews).filter(
                GoldNews.url == news_data.get('url')
            ).first()
            
            if existing:
                return existing
            
            news = GoldNews(
                title=news_data['title'],
                content=news_data.get('content'),
                source=news_data.get('source'),
                url=news_data.get('url'),
                published_at=news_data.get('published_at'),
                sentiment=SentimentType.NEUTRAL,
                keywords=news_data.get('keywords')
            )
            
            self.db.add(news)
            self.db.commit()
            
            return news
        except Exception as e:
            self.db.rollback()
            print(f"保存新闻失败: {e}")
            return None
