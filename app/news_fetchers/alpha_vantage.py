import requests
import pandas as pd
from datetime import datetime
from .base_fetcher import BaseNewsFetcher

class AlphaVantageFetcher(BaseNewsFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://www.alphavantage.co/query"
        
    def fetch_news(self, tickers, start_date, end_date):
        params = {
            'function': 'NEWS_SENTIMENT', #TOP_GAINERS_LOSERS
            'tickers': "IBM" ,#",".join(tickers),
            'apikey': self.api_key,
            'time_from': start_date.strftime('%Y%m%dT%H%M'),
            'time_to': end_date.strftime('%Y%m%dT%H%M'),
            'limit': 200  # Reduced from 1000 to stay within free tier limits
            #'topics':'technology,ipo',
        } 
        #print(",".join(tickers))
        try:
            response = requests.get(self.base_url, params=params)
            #print(response.json())
            response.raise_for_status()
            return self._parse_response(response.json())
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return pd.DataFrame()

    def _parse_response(self, data):
        if not data or 'feed' not in data:
            return pd.DataFrame()
            
        articles = []
        for item in data.get('feed', []):
            try:
                article = {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('summary', ''),  # Using 'content' as the standard column name
                    'source': item.get('source', ''),
                    'published': datetime.strptime(item['time_published'], '%Y%m%dT%H%M%S'),
                    'tickers': [t['ticker'] for t in item.get('ticker_sentiment', [])],
                    'sentiment_score': float(item.get('overall_sentiment_score', 0))
                }
                articles.append(article)
            except Exception as e:
                print(f"Error parsing article: {str(e)}")
                continue
                
        return pd.DataFrame(articles)