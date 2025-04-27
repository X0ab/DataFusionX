import requests
from datetime import datetime

class NewsAPIFetcher:
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
