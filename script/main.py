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


# Example Usage
if __name__ == "__main__":
    # Replace with your actual API keys
    api_keys = {
        'alpha_vantage': '123abc456def789ghi',   # CHANGE ME to actual key
        'yahoo_finance': '123abc456def789ghi'  # CHANGE ME 
    }
    
     