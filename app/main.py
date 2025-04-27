from datetime import datetime, timedelta
from news_fetchers.alpha_vantage import AlphaVantageFetcher
from analyzers.sentiment_analyzer import SentimentAnalyzer
from config.settings import Config
import pandas as pd

def main():
    config = Config()
    
    print("Initializing components...")
    fetcher = AlphaVantageFetcher(config.API_KEYS['alpha_vantage'])
    analyzer = SentimentAnalyzer()
    
    print("Setting time range...")
    end_date = datetime.now()
    start_date = end_date - config.TIME_WINDOW
    
    print("Fetching news...")
    news_df = fetcher.fetch_news(config.DEFAULT_TICKERS, start_date, end_date)
    
    if news_df.empty:
        print("No news articles were fetched. Check your API key and parameters.")
        return
        
    print(f"Fetched {len(news_df)} articles. Columns: {news_df.columns.tolist()}")
    
    print("Analyzing sentiment...")
    analyzed_df = analyzer.analyze_dataframe(news_df)
    
    if analyzed_df.empty:
        print("Sentiment analysis failed. Check your data.")
        return
        
    print("Analysis completed successfully!")
    print("\nSample results:")
    print(analyzed_df[['title', 'source', 'vader_compound', 'sentiment_label']].head())
    
    # Save results
    analyzed_df.to_csv('financial_news_sentiment.csv', index=False)
    print("\nResults saved to financial_news_sentiment.csv")

if __name__ == "__main__":
    main()