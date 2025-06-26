import pandas as pd
from datetime import datetime, timedelta

class DataCleaner:
    def __init__(self):
        pass
    
    def clean_data(self, df):
        """Clean the raw data"""
        if df.empty:
            return df
        
        # Convert all string fields to strings
        string_cols = ['title', 'url', 'content', 'source_name', 'type']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Ensure tickers is a list
        if 'tickers' in df.columns:
            df['tickers'] = df['tickers'].apply(
                lambda x: x if isinstance(x, list) else [])
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['url'])
        
        return df
    
    def filter_old_data(self, df, days=30):
        """Filter out data older than specified days"""
        if df.empty or 'published' not in df.columns:
            return df
        
        cutoff_date = datetime.now() - timedelta(days=days)
        return df[df['published'] >= cutoff_date]