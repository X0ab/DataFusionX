import requests
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from collections import defaultdict

# Load NLP models
nlp = spacy.load("en_core_web_sm")
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
analyzer = SentimentIntensityAnalyzer()

class FinancialNewsSentimentAnalyzer:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.news_sources = {
            'alpha_vantage': self._fetch_alpha_vantage_news,
            'yahoo_finance': self._fetch_yahoo_finance_news,
            # Add other sources as needed
        }
        
    def fetch_news(self, source, query=None, days_back=7):
        """
        Fetch news from specified source
        """
        if source not in self.news_sources:
            raise ValueError(f"Unsupported news source: {source}")
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return self.news_sources[source](query, start_date, end_date)
    
    def _fetch_alpha_vantage_news(self, tickers, start_date, end_date):
        """
        Fetch news from Alpha Vantage API
        """
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': tickers,
            'apikey': self.api_keys['alpha_vantage'],
            'time_from': start_date.strftime('%Y%m%dT%H%M'),
            'time_to': end_date.strftime('%Y%m%dT%H%M'),
            'limit': 200  # Max allowed
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        articles = []
        for item in data.get('feed', []):
            articles.append({
                'title': item.get('title'),
                'url': item.get('url'),
                'summary': item.get('summary'),
                'source': item.get('source'),
                'published': item.get('time_published'),
                'tickers': [t['ticker'] for t in item.get('ticker_sentiment', [])],
                'overall_sentiment_score': item.get('overall_sentiment_score'),
                'overall_sentiment_label': item.get('overall_sentiment_label')
            })
            
        return pd.DataFrame(articles)
    
    def _fetch_yahoo_finance_news(self, tickers, start_date, end_date):
        """
        Fetch news from Yahoo Finance (simplified example)
        """
        # Note: Yahoo Finance API may require different approach
        url = "https://yahoo-finance-api.example.com/news"
        params = {
            'symbol': tickers,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        articles = []
        for item in data.get('items', []):
            articles.append({
                'title': item.get('title'),
                'url': item.get('url'),
                'summary': item.get('content'),
                'source': 'Yahoo Finance',
                'published': item.get('pubDate'),
                'tickers': self._extract_tickers_from_text(item.get('title') + " " + item.get('content'))
            })
            
        return pd.DataFrame(articles)
    
    def _extract_tickers_from_text(self, text):
        """
        Use NER to extract company names and tickers from text
        """
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities.append(ent.text)
        
        # Simple ticker pattern matching (e.g., AAPL, MSFT)
        tokens = text.split()
        ticker_pattern = r'^[A-Z]{2,4}$'
        potential_tickers = [t for t in tokens if t.isupper() and 2 <= len(t) <= 4]
        
        return list(set(entities + potential_tickers))
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment using multiple approaches
        """
        # VADER Sentiment
        vader_scores = analyzer.polarity_scores(text)
        
        # TextBlob Sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity
        }
    
    def process_news(self, news_df):
        """
        Process news DataFrame with sentiment analysis
        """
        if news_df.empty:
            return news_df
            
        # Apply sentiment analysis
        news_df['sentiment'] = news_df['summary'].apply(
            lambda x: self.analyze_sentiment(str(x)) if pd.notnull(x) else None
        )
        
        # Expand sentiment columns
        sentiment_cols = pd.json_normalize(news_df['sentiment'])
        news_df = pd.concat([news_df.drop('sentiment', axis=1), sentiment_cols], axis=1)
        
        return news_df
    
    def aggregate_sentiment_by_ticker(self, news_df):
        """
        Aggregate sentiment scores by ticker
        """
        if news_df.empty:
            return pd.DataFrame()
            
        # Explode the tickers column to have one row per ticker
        exploded_df = news_df.explode('tickers')
        
        # Group by ticker and calculate mean sentiment
        aggregated = exploded_df.groupby('tickers').agg({
            'vader_compound': 'mean',
            'vader_positive': 'mean',
            'vader_negative': 'mean',
            'textblob_polarity': 'mean'
        }).reset_index()
        
        return aggregated
    
    def visualize_sentiment(self, aggregated_df, metric='vader_compound'):
        """
        Visualize sentiment by ticker
        """
        if aggregated_df.empty:
            print("No data to visualize")
            return
            
        aggregated_df = aggregated_df.sort_values(metric, ascending=False)
        
        plt.figure(figsize=(12, 8))
        plt.bar(aggregated_df['tickers'], aggregated_df[metric])
        plt.xlabel('Ticker')
        plt.ylabel('Sentiment Score')
        plt.title('Average Sentiment by Ticker')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


# Example Usage
if __name__ == "__main__":
    # Replace with your actual API keys
    api_keys = {
        'alpha_vantage': '123abc456def789ghi',   # CHANGE ME to actual key
        'yahoo_finance': '123abc456def789ghi'  # CHANGE ME 
    }
    
     