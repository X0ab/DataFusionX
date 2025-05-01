from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

class BaseNewsFetcher(ABC):
    def __init__(self, api_key):
        self.api_key = api_key
    
    @abstractmethod
    def fetch_news(self, tickers, start_date, end_date):
        """Fetch news for given tickers between dates"""
        pass
    
    def _parse_date(self, date_str, format_str):
        """Helper method to parse dates"""
        try:
            return datetime.strptime(date_str, format_str)
        except (ValueError, TypeError):
            return None
    
    def _filter_by_date(self, items, start_date, end_date, date_field='published'):
        """Filter items by date range"""
        return [
            item for item in items 
            if start_date <= item[date_field] <= end_date
        ]
    
    def _to_dataframe(self, items):
        """Convert list of items to DataFrame"""
        if not items:
            return pd.DataFrame()
        return pd.DataFrame(items)