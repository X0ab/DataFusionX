import os
from datetime import timedelta

class Config:
    # API Settings
    API_KEYS = {
        'alpha_vantage': os.getenv('ALPHA_VANTAGE_KEY', 'YOUR_API_KEY'),
       # 'yahoo_finance': os.getenv('YAHOO_FINANCE_KEY', 'YOUR_API_KEY')
    }
    
    # Analysis Settings
    TOPICS = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
                     'ADBE', 'INTC', 'CSCO', 'AMD', 'CRM', 'ORCL', 'IBM', 'QCOM', 'TXN', 'AVGO'],
        'Finance': ['JPM', 'BAC', 'GS', 'V', 'MA', 'PYPL'],
        'Healthcare': ['PFE', 'JNJ', 'MRK', 'UNH', 'ABBV', 'MDT', 'ABT', 'LLY', 'BMY', 'AMGN'],
        'Energy': ['XOM', 'CVX', 'SHEL', 'BP', 'COP'],
        'Retail': ['WMT', 'TGT', 'HD', 'COST', 'LOW', 'SBUX', 'MCD', 'DPZ', 'YUM'],
        'Industrial': ['HON', 'CAT', 'BA', 'MMM', 'GE'],
        'Telecom': ['VZ', 'T', 'TMUS', 'CMCSA'],
        'Consumer Goods': ['PEP', 'KO', 'PG', 'CL', 'NKE'],
        'Entertainment': ['NFLX', 'DIS']
    }

    # Combined default tickers (unique values from all sectors)
    DEFAULT_TICKERS = sorted(list({
        *TOPICS['Technology'],
        *TOPICS['Finance'],
        *TOPICS['Healthcare'],
        *TOPICS['Energy'],
        *TOPICS['Retail'],
        *TOPICS['Industrial'],
        *TOPICS['Telecom'],
        *TOPICS['Consumer Goods'],
        *TOPICS['Entertainment']
    }))

    # Comprehensive list of reliable sources
    SOURCES = [
        'Bloomberg',
        'Reuters',
        'Wall Street Journal',
        'Financial Times',
        'CNBC',
        'MarketWatch',
        'Seeking Alpha',
        'Investor\'s Business Daily',
        'Barron\'s',
        'The Economist',
        'Business Insider',
        'Yahoo Finance',
        'Motley Fool',
        'Zacks',
        'Morningstar',
        'Benzinga',
        'MarketBeat',
        'TipRanks'
    ]
    TIME_WINDOW = timedelta(days=7)
    
    # NLP Settings
    SPACY_MODEL = 'en_core_web_sm'
    SENTIMENT_THRESHOLDS = {
        'positive': 0.05,
        'negative': -0.05
    }
    
    # Visualization Settings
    COLORS = {
        'positive': '#2ecc71',
        'neutral': '#f1c40f',
        'negative': '#e74c3c'
    }

    CACHE_TTL = 3600  # 1 hour cache expiration

     
 