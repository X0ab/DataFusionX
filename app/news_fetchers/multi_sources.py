import pandas as pd
from .alpha_vantage import AlphaVantageFetcher
from .newsapi import NewsAPIFetcher
from .reddit import RedditFetcher
from .twitter import TwitterFetcher
from ..config import settings

class MultiSourceFetcher:
    def __init__(self, api_keys):
        self.fetchers = []
        
        if 'alpha_vantage' in api_keys:
            self.fetchers.append(AlphaVantageFetcher(api_keys['alpha_vantage']))
        
        if 'newsapi' in api_keys:
            self.fetchers.append(NewsAPIFetcher(api_keys['newsapi']))
        
        if 'reddit' in api_keys:
            self.fetchers.append(RedditFetcher(api_keys['reddit']))
        
        if 'twitter' in api_keys:
            self.fetchers.append(TwitterFetcher(api_keys['twitter']))
    
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch news from all enabled sources"""
        all_articles = pd.DataFrame()
        
        for fetcher in self.fetchers:
            try:
                articles = fetcher.fetch_news(tickers, start_date, end_date)
                if not articles.empty:
                    all_articles = pd.concat([all_articles, articles])
            except Exception as e:
                print(f"Error with {fetcher.__class__.__name__}: {str(e)}")
                continue
        
        return all_articles.drop_duplicates(subset=['url']).reset_index(drop=True)