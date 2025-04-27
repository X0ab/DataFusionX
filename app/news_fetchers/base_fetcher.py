from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

class BaseNewsFetcher(ABC):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = None
        
    @abstractmethod
    def fetch_news(self, tickers, start_date, end_date):
        pass
        
    def _format_date(self, date_obj):
        return date_obj.strftime('%Y-%m-%d')
    
    def _parse_response(self, response):
        raise NotImplementedError("Child classes must implement response parsing")