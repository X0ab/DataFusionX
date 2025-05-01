from datetime import datetime, timedelta
import pandas as pd
from config import settings
from fetchers.multi_source import MultiSourceFetcher
from processors.sentiment import SentimentAnalyzer
from processors.cleaner import DataCleaner
from storage.database import DatabaseStorage

class FinancialNewsAggregator:
    def __init__(self):
        self.fetcher = MultiSourceFetcher(settings.API_KEYS)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_cleaner = DataCleaner()
        self.storage = DatabaseStorage()
    
    def fetch_and_store_news(self, tickers, days_back=7):
        """Main method to fetch, process and store news"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"Fetching news for {tickers} from {start_date} to {end_date}")
        
        # Fetch news from all sources
        raw_data = self.fetcher.fetch_news(tickers, start_date, end_date)
        
        if raw_data.empty:
            print("No new data fetched.")
            return
        
        print(f"Fetched {len(raw_data)} items")
        
        # Clean data
        cleaned_data = self.data_cleaner.clean_data(raw_data)
        
        # Analyze sentiment
        analyzed_data = self.sentiment_analyzer.analyze_dataframe(cleaned_data)
        
        # Store data
        self.storage.save_data(analyzed_data)
        
        # Cleanup old data
        self.storage.cleanup_old_data(settings.DATA_STORAGE_DAYS)
        
        print(f"Successfully stored {len(analyzed_data)} items")
    
    def get_news(self, tickers=None, days_back=7):
        """Retrieve news from storage"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return self.storage.load_data(tickers, start_date, end_date)

if __name__ == "__main__":
    aggregator = FinancialNewsAggregator()
    
    # Example usage
    tickers_to_track = ['IBM','AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Fetch and store new data
    aggregator.fetch_and_store_news(tickers_to_track, days_back=3)
    
    # Retrieve stored data
    stored_data = aggregator.get_news(tickers_to_track, days_back=3)
    
    if not stored_data.empty:
        print("\nStored data sample:")
        print(stored_data[['source', 'title', 'published', 'sentiment_score']].head())
    else:
        print("No data found in storage.")