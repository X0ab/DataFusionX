import requests
import pandas as pd
from datetime import datetime
from config import settings
from .base_fetcher import BaseNewsFetcher
from datetime import datetime, timedelta

class AlphaVantageFetcher(BaseNewsFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://www.alphavantage.co/query"
        self.max_tickers = settings.MAX_TICKERS_PER_REQUEST
    
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch news from Alpha Vantage API"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Default to 7 days if not provided
        
        # Format dates for Alpha Vantage API
        time_from = start_date.strftime('%Y%m%dT%H%M')
        time_to = end_date.strftime('%Y%m%dT%H%M')
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': ",".join(tickers[:self.max_tickers]),
            'apikey': self.api_key,
            'time_from': time_from,
            'time_to': time_to,
            'limit': 200  # Reduced from 1000 to stay within free tier limits
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return self._parse_response(response.json(), tickers , start_date, end_date)
        except Exception as e:
            print(f"AlphaVantage error: {str(e)}")
            return pd.DataFrame()

    def _parse_response(self, data, tickers, start_date, end_date):
        """Parse Alpha Vantage response"""
        if not data or 'feed' not in data:
            return pd.DataFrame()
            
        articles = []
        for item in data.get('feed', []):
            try:
                published_date = self._parse_date(item['time_published'], '%Y%m%dT%H%M%S')
                if not published_date:
                    continue
                    
                article = {
                    'source': 'alpha_vantage',
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('summary', ''),
                    'source_name': item.get('source', ''),
                    'published': published_date,
                    'tickers': [t['ticker'] for t in item.get('ticker_sentiment', [])],
                    'sentiment_score': float(item.get('overall_sentiment_score', 0)),
                    'type': 'news'
                }
                articles.append(article)
            except Exception as e:
                print(f"Error parsing AlphaVantage article: {str(e)}")
                continue
                
        return self._to_dataframe(self._filter_by_date(articles, start_date, end_date))