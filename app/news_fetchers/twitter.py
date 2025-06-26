import tweepy
import pandas as pd
from datetime import datetime
from ..config import settings
from .base_fetcher import BaseNewsFetcher

class TwitterFetcher(BaseNewsFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.auth = tweepy.OAuthHandler(
            api_key['consumer_key'],
            api_key['consumer_secret']
        )
        self.auth.set_access_token(
            api_key['access_token'],
            api_key['access_token_secret']
        )
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True)
    
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch tweets from Twitter"""
        query = " OR ".join([f"${ticker}" for ticker in tickers])
        tweets = []
        
        try:
            # Note: Free Twitter API has limited search capabilities
            for tweet in tweepy.Cursor(
                self.api.search_tweets,
                q=query,
                lang='en',
                result_type='recent',
                tweet_mode='extended',
                until=end_date.strftime('%Y-%m-%d')
            ).items(1000):  # Max we can reasonably get without hitting limits
                if start_date <= tweet.created_at <= end_date:
                    tweets.append(tweet)
            
            return self._parse_response(tweets, tickers)
        except Exception as e:
            print(f"Twitter error: {str(e)}")
            return pd.DataFrame()

    def _parse_response(self, tweets, tickers):
        """Parse Twitter tweets"""
        articles = []
        for tweet in tweets:
            try:
                text = tweet.full_text
                article = {
                    'source': 'twitter',
                    'title': text[:100] + "..." if len(text) > 100 else text,
                    'url': f"https://twitter.com/user/status/{tweet.id}",
                    'content': text,
                    'source_name': tweet.user.screen_name,
                    'published': tweet.created_at,
                    'tickers': [t for t in tickers if t.lower() in text.lower()],
                    'sentiment_score': 0,  # Will be calculated later
                    'type': 'social'
                }
                articles.append(article)
            except Exception as e:
                print(f"Error parsing tweet: {str(e)}")
                continue
                
        return self._to_dataframe(articles)