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
 