from textblob import TextBlob
import pandas as pd

class SentimentAnalyzer:
    def __init__(self):
        pass
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
    
    def analyze_dataframe(self, df):
        """Add sentiment analysis to DataFrame"""
        if df.empty:
            return df
        
        # Only analyze items without existing sentiment scores
        mask = (df['sentiment_score'] == 0) & (~df['content'].isna())
        df.loc[mask, 'sentiment_score'] = df[mask]['content'].apply
        (lambda x: self.analyze_sentiment(str(x)))
        
        return df