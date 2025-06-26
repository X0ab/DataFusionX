import praw
import pandas as pd
from datetime import datetime
from ..config import settings
from .base_fetcher import BaseNewsFetcher

class RedditFetcher(BaseNewsFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.reddit = praw.Reddit(
            client_id=api_key['client_id'],
            client_secret=api_key['client_secret'],
            user_agent=api_key['user_agent']
        )
    
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch posts from Reddit"""
        query = " OR ".join([f"${ticker}" for ticker in tickers])
        submissions = []
        
        try:
            # Search in relevant subreddits
            subreddits = ['stocks', 'investing', 'wallstreetbets', 'finance']
            
            for subreddit in subreddits:
                for submission in self.reddit.subreddit(subreddit).search(
                    query,
                    sort='new',
                    time_filter='year',  # Max timeframe
                    limit=100
                ):
                    created_date = datetime.fromtimestamp(submission.created_utc)
                    if start_date <= created_date <= end_date:
                        submissions.append(submission)
            
            return self._parse_response(submissions, tickers)
        except Exception as e:
            print(f"Reddit error: {str(e)}")
            return pd.DataFrame()

    def _parse_response(self, submissions, tickers):
        """Parse Reddit submissions"""
        articles = []
        for submission in submissions:
            try:
                created_date = datetime.fromtimestamp(submission.created_utc)
                article = {
                    'source': 'reddit',
                    'title': submission.title,
                    'url': f"https://reddit.com{submission.permalink}",
                    'content': submission.selftext,
                    'source_name': f"r/{submission.subreddit.display_name}",
                    'published': created_date,
                    'tickers': [t for t in tickers if t.lower() in submission.title.lower()],
                    'sentiment_score': 0,  # Will be calculated later
                    'type': 'social'
                }
                articles.append(article)
            except Exception as e:
                print(f"Error parsing Reddit submission: {str(e)}")
                continue
                
        return self._to_dataframe(articles)