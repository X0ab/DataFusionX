import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Set up page configuration
st.set_page_config(
    page_title="Financial News Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

# Configuration
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "financial_news.csv")

# API Configuration - Replace with your actual keys
API_CONFIG = {
    "newsapi": "bbf76eb5888b480d8d910a091c56ec3d",  # Get from https://newsapi.org
    "alphavantage": "ADH8ZGOF8G6HLADE",  # Get from https://www.alphavantage.co
    "finnhub": "d09r1p9r01qus8rest20d09r1p9r01qus8rest2g"  # Get from https://finnhub.io
}

# Sample tickers by sector
TOPICS = {
    "Technology": ["IBM","AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "Finance": ["JPM", "BAC", "GS", "MS", "V"],
    "Healthcare": ["PFE", "JNJ", "UNH", "MRK", "ABT"]
}

def fetch_newsapi_articles(tickers, days_back):
    """Fetch articles from NewsAPI using direct API calls"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        base_url = "https://newsapi.org/v2/everything"
        all_articles = []
        
        for ticker in tickers:
            params = {
                "q": ticker,
                "from": start_date.strftime('%Y-%m-%d'),
                "to": end_date.strftime('%Y-%m-%d'),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
                "apiKey": API_CONFIG["newsapi"]
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raises exception for bad status codes
            data = response.json()
            
            # Add ticker information to each article
            articles = data.get('articles', [])
            for article in articles:
                article['related_tickers'] = [ticker]
            all_articles.extend(articles)
        
        return pd.DataFrame(all_articles)
    except requests.exceptions.RequestException as e:
        st.warning(f"NewsAPI request failed: {str(e)}")
    except Exception as e:
        st.warning(f"NewsAPI Error: {str(e)}")
    return pd.DataFrame()

def fetch_alphavantage_news(tickers, days_back):
    """Fetch news from Alpha Vantage with enhanced error handling"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        base_url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": API_CONFIG["alphavantage"],
            "tickers": ",".join(tickers),
            "time_from": start_date.strftime('%Y%m%dT0000'),
            "time_to": end_date.strftime('%Y%m%dT2359'),
            "limit": 1000  # Max allowed by Alpha Vantage
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'feed' in data:
            return pd.DataFrame(data['feed'])
        st.warning("AlphaVantage returned no news feed")
    except requests.exceptions.RequestException as e:
        st.warning(f"AlphaVantage request failed: {str(e)}")
    except Exception as e:
        st.warning(f"AlphaVantage processing error: {str(e)}")
    return pd.DataFrame()

