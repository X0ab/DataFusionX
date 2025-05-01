import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys (replace with your actual keys or use environment variables)
API_KEYS = {
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_KEY', 'alpha_vantage'),
    'newsapi': os.getenv('NEWSAPI_KEY', 'your_newsapi_key'),
    'reddit': {
        'client_id': os.getenv('REDDIT_CLIENT_ID', 'your_reddit_client_id'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'your_reddit_client_secret'),
        'user_agent': os.getenv('REDDIT_USER_AGENT', 'financial_news_scraper')
    },
    'twitter': {
        'consumer_key': os.getenv('TWITTER_CONSUMER_KEY', 'your_twitter_consumer_key'),
        'consumer_secret': os.getenv('TWITTER_CONSUMER_SECRET', 'your_twitter_consumer_secret'),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN', 'your_twitter_access_token'),
        'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', 'your_twitter_access_token_secret')
    }
}

# Database configuration
DATABASE_CONFIG = {
    'db_path': os.path.join(BASE_DIR, 'data', 'news_data.db'),
    'table_name': 'financial_news'
}

# Other settings
MAX_TICKERS_PER_REQUEST = 5  # Limit to avoid API rate limits
DATA_STORAGE_DAYS = 30       # How many days of data to keep
CACHE_TTL = 3600             # Cache time-to-live in seconds
DEFAULT_TICKERS = ['IBM','AAPL', 'MSFT', 'GOOG']  # Add default tickers
TIME_WINDOW = timedelta(days=7)  # Default time window


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    API_KEYS = API_KEYS  # Reuse the same dictionary
    DATABASE_CONFIG = DATABASE_CONFIG
    MAX_TICKERS_PER_REQUEST = 5
    DATA_STORAGE_DAYS = 30
    CACHE_TTL = 3600
    DEFAULT_TICKERS = ['IBM','AAPL', 'MSFT', 'GOOG']
    TIME_WINDOW = timedelta(days=7)

    TOPICS = {
            'Technology': ['IBM','AAPL', 'MSFT', 'GOOG', 'AMZN', 'META'],
            'Finance': ['JPM', 'BAC', 'GS', 'MS', 'V'],
            'Healthcare': ['PFE', 'JNJ', 'UNH', 'MRK', 'ABT'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG']
        }
        
    SOURCES = [
        'Bloomberg',
        'Reuters',
        'Wall Street Journal',
        'Financial Times',
        'CNBC',
        'MarketWatch',
        'Seeking Alpha',
        "Investor's Business Daily",
        "Barron's"
    ]


