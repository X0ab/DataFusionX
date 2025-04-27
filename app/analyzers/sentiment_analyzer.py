from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import pandas as pd
from config.settings import Config

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.config = Config()
        
    def analyze_text(self, text):
        if not text or not isinstance(text, str):
            return {
                'vader_compound': 0,
                'vader_pos': 0,
                'vader_neg': 0,
                'textblob_polarity': 0,
                'textblob_subjectivity': 0,
                'sentiment_label': 'neutral'
            }
            
        vader_scores = self.vader.polarity_scores(text)
        blob = TextBlob(text)
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_pos': vader_scores['pos'],
            'vader_neg': vader_scores['neg'],
            'textblob_polarity': blob.sentiment.polarity,
            'textblob_subjectivity': blob.sentiment.subjectivity,
            'sentiment_label': self._classify_sentiment(vader_scores['compound'])
        }
    
    def _classify_sentiment(self, score):
        if score >= self.config.SENTIMENT_THRESHOLDS['positive']:
            return 'positive'
        elif score <= self.config.SENTIMENT_THRESHOLDS['negative']:
            return 'negative'
        return 'neutral'
    
    def analyze_dataframe(self, df):
        if df.empty:
            return pd.DataFrame()
            
        df = df.copy()
        
        # Ensure required columns exist
        if 'content' not in df.columns:
            df['content'] = ''
            
        # Apply sentiment analysis
        df['sentiment'] = df['content'].apply(self.analyze_text)
        
        # Expand sentiment columns
        sentiment_cols = pd.json_normalize(df['sentiment'])
        result_df = pd.concat([df.drop('sentiment', axis=1), sentiment_cols], axis=1)
        
        return result_df