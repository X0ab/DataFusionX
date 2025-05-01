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

def fetch_finnhub_news(tickers, days_back):
    """Fetch news from Finnhub with better error handling"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        base_url = "https://finnhub.io/api/v1/company-news"
        all_articles = []
        
        for ticker in tickers:
            params = {
                "symbol": ticker,
                "from": start_date.strftime('%Y-%m-%d'),
                "to": end_date.strftime('%Y-%m-%d'),
                "token": API_CONFIG["finnhub"]
            }
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            articles = response.json()
            
            if isinstance(articles, list):
                # Add ticker info to each article
                for article in articles:
                    article['related_tickers'] = [ticker]
                all_articles.extend(articles)
        
        return pd.DataFrame(all_articles)
    except requests.exceptions.RequestException as e:
        st.warning(f"Finnhub request failed: {str(e)}")
    except Exception as e:
        st.warning(f"Finnhub processing error: {str(e)}")
    return pd.DataFrame()

def normalize_data(df, source):
    """Normalize data from different APIs to common format with better type handling"""
    if df.empty:
        return df
    
    try:
        if source == "newsapi":
            normalized = pd.DataFrame({
                'title': df['title'].astype(str),
                'content': df['description'].fillna('').astype(str),
                'source': df['source'].apply(
                    lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else str(x)),
                'published': pd.to_datetime(df['publishedAt'], errors='coerce'),
                'url': df['url'].astype(str),
                'urlToImage': df['urlToImage'].fillna('').astype(str),
                'tickers': df['related_tickers'].apply(lambda x: x if isinstance(x, list) else [])
            })
        
        elif source == "alphavantage":
            normalized = pd.DataFrame({
                'title': df['title'].astype(str),
                'content': df['summary'].fillna('').astype(str),
                'source': df['source'].fillna('Unknown').astype(str),
                'published': pd.to_datetime(df['time_published'], errors='coerce'),
                'url': df['url'].astype(str),
                'urlToImage': '',
                'tickers': df.get('ticker_sentiment', []).apply(
                    lambda x: [item['ticker'] for item in x] if isinstance(x, list) else [])
            })
        
        elif source == "finnhub":
            normalized = pd.DataFrame({
                'title': df['headline'].astype(str),
                'content': df['summary'].fillna('').astype(str),
                'source': df['source'].fillna('Unknown').astype(str),
                'published': pd.to_datetime(df['datetime'], unit='s', errors='coerce'),
                'url': df['url'].astype(str),
                'urlToImage': df['image'].fillna('').astype(str),
                'tickers': df['related_tickers'].apply(lambda x: x if isinstance(x, list) else [])
            })
        
        # Clean and filter the normalized data
        normalized = normalized.dropna(subset=['published'])
        normalized = normalized[normalized['published'].notna()]
        return normalized
    
    except Exception as e:
        st.warning(f"Error normalizing {source} data: {str(e)}")
        return pd.DataFrame()

def update_data_store(new_data):
    """Update or create the CSV file with new data, with better deduplication"""
    try:
        if os.path.exists(DATA_FILE):
            existing_data = pd.read_csv(DATA_FILE, parse_dates=['published'])
            # Combine and deduplicate based on title + source + published date
            combined_data = pd.concat([existing_data, new_data])
            combined_data = combined_data.drop_duplicates(
                subset=['title', 'source', 'published'],
                keep='last'
            )
        else:
            combined_data = new_data
        
        # Ensure directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save with proper date formatting
        combined_data.to_csv(DATA_FILE, index=False, date_format='%Y-%m-%d %H:%M:%S')
        return combined_data
    
    except Exception as e:
        st.error(f"Error updating data store: {str(e)}")
        return new_data

def analyze_sentiment(df):
    """Perform sentiment analysis with enhanced text preprocessing"""
    if df.empty:
        return df
    
    try:
        sentiments = []
        for content in df['content'].fillna(''):
            # Basic text cleaning
            clean_content = ' '.join(str(content).split())  # Remove extra whitespace
            sentiments.append(analyzer.polarity_scores(clean_content))
        
        sentiment_df = pd.DataFrame(sentiments)
        df = pd.concat([df, sentiment_df], axis=1)
        
        # Add sentiment label with more nuanced thresholds
        df['sentiment_label'] = df['compound'].apply(
            lambda x: 'positive' if x > 0.15 else (
                'negative' if x < -0.15 else 'neutral'
            )
        )
        
        return df
    
    except Exception as e:
        st.error(f"Sentiment analysis failed: {str(e)}")
        return df

