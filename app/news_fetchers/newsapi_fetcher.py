import requests
from datetime import datetime
import requests
import pandas as pd
from datetime import datetime
from ..config import settings
from .base_fetcher import BaseNewsFetcher
class NewsFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = 'https://newsapi.org/v2/top-headlines?country=us&category=business' #everything
        
        # Simple ticker -> company name map
        self.ticker_name_map = {
            'IBM': 'IBM',
            'AAPL': 'apple',
            'GOOG': 'Google',
            'MSFT': 'Microsoft',
            'TSLA': 'Tesla',
            'AMZN': 'Amazon',
            'META': 'Meta Platforms',
            'NFLX': 'Netflix',
            'NVDA': 'NVIDIA',
            'AMD': 'Advanced Micro Devices'
            # you can extend this!
        }

    def fetch_news(self, tickers, start_date, end_date):
        all_articles = []

        for ticker in tickers:
            query = self.ticker_name_map.get(ticker, ticker)  # Try company name, fallback to ticker
            params = {
                'q': query,
                #'from': start_date.strftime('%Y-%m-%d'),
                #'to': end_date.strftime('%Y-%m-%d'),
                #'language': 'en',
                #'sortBy': 'relevancy',
                #'pageSize': 100,  # Max per request
                'apiKey': "bbf76eb5888b480d8d910a091c56ec3d" #self.api_key
            }

            response = requests.get(self.endpoint, params=params)
            
            if response.status_code == 200 or response['status'] == 'ok':
                data = response.json()
                articles = data.get('articles', [])
                print(articles)
                for article in articles:
                    # Normalize the format
                    all_articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'publishedAt': article.get('publishedAt'),
                        'source': article.get('source', {}).get('name'),
                        'url': article.get('url'),
                        'image': article.get('urlToImage'),
                        'tickers': [ticker] , # Associate back
                        'content': article.get('content'),
                    })
            else:
                print(f"Failed to fetch news for {query}: {response.status_code}")

        return all_articles

    def fetch_news_by_keywords(self, tickers, start_date, end_date):
        all_articles = []

        for ticker in tickers:
            query = self.ticker_name_map.get(ticker, ticker)  # Try company name, fallback to ticker
            params = {
                'q': query,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 100,  # Max per request
                'apiKey': self.api_key #"bbf76eb5888b480d8d910a091c56ec3d" #
            }

            response = requests.get(self.endpoint, params=params)
            #print(response)
            if response.status_code == 200 or response['status'] == 'ok':
                data = response.json()
                articles = data.get('articles', [])
                #print(articles)
                for article in articles:
                    # Normalize the format
                    all_articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'publishedAt': article.get('publishedAt'),
                        'source': article.get('source', {}).get('name'),
                        'url': article.get('url'),
                        'urlToImage': article.get('urlToImage'),
                        #'tickers': [ticker] , # Associate back
                        'content': article.get('content'),
                    })
            else:
                print(f"Failed to fetch news for {query}: {response.status_code}")

        return all_articles



class NewsAPIFetcher(BaseNewsFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch news from NewsAPI"""
        query = " OR ".join([f"${ticker}" for ticker in tickers[:settings.MAX_TICKERS_PER_REQUEST]])
        params = {
            'q': query,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apiKey': self.api_key,
            'pageSize': 100,  # Max for free tier
            'language': 'en',
            'sortBy': 'publishedAt'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return self._parse_response(response.json())
        except Exception as e:
            print(f"NewsAPI error: {str(e)}")
            return pd.DataFrame()

    def _parse_response(self, data):
        """Parse NewsAPI response"""
        if not data or 'articles' not in data:
            return pd.DataFrame()
            
        articles = []
        for item in data.get('articles', []):
            try:
                published_date = self._parse_date(item['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                if not published_date:
                    continue
                    
                article = {
                    'source': 'newsapi',
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', item.get('description', '')),
                    'source_name': item.get('source', {}).get('name', ''),
                    'published': published_date,
                    'tickers': [],  # NewsAPI doesn't provide ticker info
                    'sentiment_score': 0,  # Will be calculated later
                    'type': 'news'
                }
                articles.append(article)
            except Exception as e:
                print(f"Error parsing NewsAPI article: {str(e)}")
                continue
                
        return self._to_dataframe(articles)