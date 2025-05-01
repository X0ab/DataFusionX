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
    """Normalize data from different APIs to common format with better datetime handling"""
    if df.empty:
        return df
    
    try:
        if source == "newsapi":
            normalized = pd.DataFrame({
                'title': df['title'].astype(str),
                'content': df['description'].fillna('').astype(str),
                'source': df['source'].apply(
                    lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else str(x)),
                'published': pd.to_datetime(df['publishedAt'], utc=True, errors='coerce'),
                'url': df['url'].astype(str),
                'urlToImage': df['urlToImage'].fillna('').astype(str),
                'tickers': df['related_tickers'].apply(lambda x: x if isinstance(x, list) else [])
            })
        
        elif source == "alphavantage":
            normalized = pd.DataFrame({
                'title': df['title'].astype(str),
                'content': df['summary'].fillna('').astype(str),
                'source': df['source'].fillna('Unknown').astype(str),
                'published': pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S', utc=True, errors='coerce'),
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
                'published': pd.to_datetime(df['datetime'], unit='s', utc=True, errors='coerce'),
                'url': df['url'].astype(str),
                'urlToImage': df['image'].fillna('').astype(str),
                'tickers': df['related_tickers'].apply(lambda x: x if isinstance(x, list) else [])
            })
        
        # Clean and filter the normalized data
        normalized = normalized[normalized['published'].notna()]
        return normalized
    
    except Exception as e:
        st.warning(f"Error normalizing {source} data: {str(e)}")
        return pd.DataFrame()
def update_data_store(new_data):
    """Update or create the CSV file with new data, with better datetime handling"""
    try:
        if os.path.exists(DATA_FILE):
            existing_data = pd.read_csv(DATA_FILE)
            # Convert published column to datetime if it's not already
            if 'published' in existing_data.columns:
                existing_data['published'] = pd.to_datetime(existing_data['published'], utc=True, errors='coerce')
            # Combine and deduplicate
            combined_data = pd.concat([existing_data, new_data])
            combined_data = combined_data.drop_duplicates(
                subset=['title', 'source', 'published'],
                keep='last'
            )
        else:
            combined_data = new_data
        
        # Ensure directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save with ISO format datetime
        combined_data.to_csv(DATA_FILE, index=False)
        return combined_data
    
    except Exception as e:
        st.error(f"Error updating data store: {str(e)}")
        return new_data

def analyze_sentiment(df):
    """Perform sentiment analysis with proper index handling"""
    if df.empty:
        return df
    
    try:
        # Reset index to ensure uniqueness
        df = df.reset_index(drop=True)
        
        # Ensure we have text content to analyze
        if 'content' not in df.columns:
            st.warning("No content column available for sentiment analysis")
            return df
        
        sentiments = []
        for content in df['content'].fillna(''):
            try:
                # Basic text cleaning
                clean_content = ' '.join(str(content).split())  # Remove extra whitespace
                sentiments.append(analyzer.polarity_scores(clean_content))
            except Exception as e:
                st.warning(f"Error analyzing sentiment for content: {str(e)}")
                # Append neutral sentiment if analysis fails
                sentiments.append({'neg': 0, 'neu': 1, 'pos': 0, 'compound': 0})
        
        sentiment_df = pd.DataFrame(sentiments)
        
        # Check if we got any sentiment data
        if not sentiment_df.empty:
            # Reset index before concatenation
            sentiment_df = sentiment_df.reset_index(drop=True)
            df = df.reset_index(drop=True)
            
            # Concatenate with the original DataFrame
            df = pd.concat([df, sentiment_df], axis=1)
            
            # Add sentiment label with more nuanced thresholds
            if 'compound' in df.columns:
                df['sentiment_label'] = df['compound'].apply(
                    lambda x: 'positive' if x > 0.15 else (
                        'negative' if x < -0.15 else 'neutral'
                    )
                )
            else:
                st.warning("No compound sentiment scores were generated")
                df['sentiment_label'] = 'neutral'
                df['compound'] = 0
        else:
            st.warning("Sentiment analysis returned no results")
            df['sentiment_label'] = 'neutral'
            df['compound'] = 0
            df['neg'] = 0
            df['neu'] = 0
            df['pos'] = 0
        
        return df
    
    except Exception as e:
        st.error(f"Sentiment analysis failed: {str(e)}")
        # Add default sentiment columns if analysis completely fails
        if 'compound' not in df.columns:
            df['compound'] = 0
            df['neg'] = 0
            df['neu'] = 0
            df['pos'] = 0
            df['sentiment_label'] = 'neutral'
        return df
    
      
def show_sidebar():
    """Render the sidebar controls with enhanced layout"""
    with st.sidebar:
        st.header("📊 Analysis Settings")
        
        # Topic selection with icons
        selected_topic = st.selectbox(
            "Select Market Sector",
            options=list(TOPICS.keys()),
            index=0,
            help="Choose a sector to analyze"
        )
        
        # Ticker selection with search
        selected_tickers = st.multiselect(
            "Select Tickers",
            options=TOPICS[selected_topic],
            default=TOPICS[selected_topic][:3],
            help="Select at least one ticker symbol"
        )
        
        # Time period with date display
        days_back = st.slider(
            "Analysis Period (Days)",
            1, 30, 7,
            help="How many days of news to analyze"
        )
        st.caption(f"Analyzing from {(datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        # Source selection with icons
        selected_sources = st.multiselect(
            "Data Sources",
            options=["NewsAPI", "AlphaVantage", "Finnhub"],
            default=["NewsAPI", "AlphaVantage"],
            help="Select which APIs to query"
        )
        
        # Sentiment filter with explanation
        min_sentiment = st.slider(
            "Minimum Sentiment Score",
            -1.0, 1.0, -1.0,
            help="Filter out articles with sentiment below this threshold"
        )
        
        return selected_tickers, selected_sources, days_back, min_sentiment

def show_main_content(df, min_sentiment):
    """Render the main dashboard content with enhanced visualizations"""
    if df.empty:
        st.warning("No news articles match your filters")
        return
    
    if 'compound' not in df.columns:
        st.error("Sentiment analysis data not available - showing all articles")
        filtered_df = df
    else:
        # Filter by sentiment
        filtered_df = df[df['compound'] >= min_sentiment]

    # Filter by sentiment
    #df = df[df['compound'] >= min_sentiment]
    if filtered_df.empty:
        st.warning("No articles match your sentiment filter")
        return
    
    # Convert published column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(filtered_df['published']):
        filtered_df['published'] = pd.to_datetime(filtered_df['published'], utc=True, errors='coerce')
    
    # Extract date for grouping
    filtered_df['date'] = filtered_df['published'].dt.date


    # Display metrics with icons
    st.subheader("📊 Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)
    avg_sentiment = df['compound'].mean()
    col1.metric("📈 Average Sentiment", 
               f"{avg_sentiment:.2f}", 
               "Positive" if avg_sentiment > 0 else "Negative",
               delta_color="normal")
    col2.metric("📰 Total Articles", len(df))
    col3.metric("🏢 Sources", df['source'].nunique())
    col4.metric("💵 Tickers Covered", df['tickers'].explode().nunique())
    
    # Main tabs with enhanced UI
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Sentiment Trends", 
        "🏷️ Ticker Analysis", 
        "📰 Source Insights", 
        "📋 Article Data"
    ])
    
    with tab1:
        st.subheader("📈 Sentiment Over Time")
        df['date'] = pd.to_datetime(df['published']).dt.date
        daily_sentiment = df.groupby(['date', 'sentiment_label']).size().unstack().fillna(0)
        
        fig1 = px.area(
            daily_sentiment,
            title="Daily Sentiment Trend",
            labels={'value': 'Number of Articles', 'date': 'Date'},
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#f1c40f',
                'negative': '#e74c3c'
            }
        )
        fig1.update_layout(
            hovermode="x unified",
            legend_title="Sentiment"
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("📊 Sentiment Distribution")
        fig2 = px.histogram(
            df,
            x='compound',
            nbins=20,
            title="Sentiment Score Distribution",
            labels={'compound': 'Sentiment Score'},
            color='sentiment_label',
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#f1c40f',
                'negative': '#e74c3c'
            }
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("🏷️ Ticker Sentiment Comparison")
        try:
            exploded_df = df.explode('tickers')
            exploded_df = exploded_df[exploded_df['tickers'].notna()]
            
            if not exploded_df.empty:
                ticker_sentiment = exploded_df.groupby('tickers', observed=True).agg(
                    mean_sentiment=('compound', 'mean'),
                    article_count=('title', 'count')
                ).sort_values('mean_sentiment')
                
                fig = px.bar(
                    ticker_sentiment,
                    x='mean_sentiment',
                    y=ticker_sentiment.index,
                    orientation='h',
                    color='mean_sentiment',
                    color_continuous_scale='RdYlGn',
                    title="Average Sentiment by Ticker",
                    labels={'mean_sentiment': 'Sentiment Score', 'index': 'Ticker'},
                    hover_data=['article_count'],
                    height=600
                )
                fig.update_layout(
                    coloraxis_showscale=False,
                    yaxis={'categoryorder': 'total ascending'},
                    xaxis_range=[-1, 1]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No ticker data available after processing")
        except Exception as e:
            st.error(f"Error in ticker comparison: {str(e)}")
    
    with tab3:
        st.subheader("📰 Source Analysis")
        
        source_col1, source_col2 = st.columns(2)
        
        with source_col1:
            st.markdown("#### Top Sources by Volume")
            source_counts = df['source'].value_counts().nlargest(10)
            fig1 = px.pie(
                source_counts,
                names=source_counts.index,
                values=source_counts.values,
                title="Top News Sources"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with source_col2:
            st.markdown("#### Sentiment by Source")
            source_stats = df.groupby('source').agg({
                'compound': 'mean',
                'title': 'count'
            }).sort_values('title', ascending=False).head(10)
            
            fig2 = px.bar(
                source_stats,
                x='compound',
                y=source_stats.index,
                orientation='h',
                color='compound',
                color_continuous_scale='RdYlGn',
                title="Average Sentiment by Source",
                labels={'compound': 'Avg. Sentiment', 'y': 'Source'},
                hover_data=['title']
            )
            fig2.update_layout(
                coloraxis_showscale=True,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_range=[-1, 1]
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab4:
        st.subheader("📋 Article Data")
        
        # Enhanced filtering options
        with st.expander("🔍 Filter Options", expanded=True):
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                source_filter = st.multiselect(
                    "Filter by Source",
                    options=df['source'].unique(),
                    default=df['source'].unique()[:3]
                )
            
            with filter_col2:
                sentiment_filter = st.select_slider(
                    "Filter by Sentiment",
                    options=['negative', 'neutral', 'positive'],
                    value=['negative', 'positive']
                )
        
        # Apply filters
        filtered_df = df[
            (df['source'].isin(source_filter)) & 
            (df['sentiment_label'].isin(sentiment_filter))
        ].sort_values('published', ascending=False)
        
        # Display data with enhanced formatting
        st.dataframe(
            filtered_df[['published', 'title', 'source', 'tickers', 'compound', 'sentiment_label']],
            column_config={
                "published": st.column_config.DatetimeColumn(
                    "Date",
                    format="YYYY-MM-DD HH:mm"
                ),
                "title": "Headline",
                "source": "Source",
                "tickers": st.column_config.ListColumn(
                    "Tickers",
                    help="Related ticker symbols"
                ),
                "compound": st.column_config.NumberColumn(
                    "Sentiment",
                    format="%.2f",
                    help="VADER compound sentiment score (-1 to 1)"
                ),
                "sentiment_label": st.column_config.TextColumn(
                    "Label",
                    help="Sentiment classification"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

def main():
    """Main application function with enhanced setup checks"""
    st.title("📰 Financial News Sentiment Dashboard")
    
    # Check for API keys
    if any(val.startswith('your_') or val == '' for val in API_CONFIG.values()):
        st.error("API Keys Not Configured")
        st.markdown("""
        Please configure your API keys in the `API_CONFIG` dictionary:
        1. Get a [NewsAPI key](https://newsapi.org)
        2. Get an [Alpha Vantage key](https://www.alphavantage.co)
        3. Get a [Finnhub key](https://finnhub.io)
        """)
        st.code("""
        API_CONFIG = {
            "newsapi": "your_actual_key_here",
            "alphavantage": "your_actual_key_here",
            "finnhub": "your_actual_key_here"
        }
        """)
        return
    
    # Check for required packages
    try:
        import requests
        import pandas
        import plotly
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError as e:
        st.error("Missing Required Packages")
        st.markdown(f"""
        Error: {str(e)}
        
        Install required packages with:
        ```bash
        pip install requests pandas plotly vaderSentiment
        ```
        """)
        return
    
    # Get user inputs from sidebar
    tickers, sources, days_back, min_sentiment = show_sidebar()
    
    if not tickers:
        st.warning("Please select at least one ticker")
        return
    
    if not sources:
        st.warning("Please select at least one data source")
        return
    
    # Fetch and process data
    with st.spinner("🔍 Fetching and analyzing news data..."):
        all_data = pd.DataFrame()
        
        if "NewsAPI" in sources:
            with st.expander("NewsAPI Progress", expanded=False):
                st.info("Fetching from NewsAPI...")
                newsapi_data = fetch_newsapi_articles(tickers, days_back)
                st.info(f"Found {len(newsapi_data)} raw articles")
                newsapi_normalized = normalize_data(newsapi_data, "newsapi")
                st.info(f"Normalized to {len(newsapi_normalized)} articles")
                all_data = pd.concat([all_data, newsapi_normalized], ignore_index=True)
        
        if "AlphaVantage" in sources:
            with st.expander("AlphaVantage Progress", expanded=False):
                st.info("Fetching from AlphaVantage...")
                av_data = fetch_alphavantage_news(tickers, days_back)
                st.info(f"Found {len(av_data)} raw articles")
                av_normalized = normalize_data(av_data, "alphavantage")
                st.info(f"Normalized to {len(av_normalized)} articles")
                all_data = pd.concat([all_data, av_normalized], ignore_index=True)
        
        if "Finnhub" in sources:
            with st.expander("Finnhub Progress", expanded=False):
                st.info("Fetching from Finnhub...")
                finnhub_data = fetch_finnhub_news(tickers, days_back)
                st.info(f"Found {len(finnhub_data)} raw articles")
                finnhub_normalized = normalize_data(finnhub_data, "finnhub")
                st.info(f"Normalized to {len(finnhub_normalized)} articles")
                all_data = pd.concat([all_data, finnhub_normalized], ignore_index=True)
        
        if not all_data.empty:
            # Update data store
            with st.spinner("💾 Saving data..."):
                updated_data = update_data_store(all_data)
                st.success(f"Data store updated with {len(updated_data)} total articles")
            
            # Analyze sentiment
            with st.spinner("🧠 Analyzing sentiment..."):
                analyzed_data = analyze_sentiment(updated_data)
                st.success("Sentiment analysis complete")
            
            # Show results
            show_main_content(analyzed_data, min_sentiment)
        else:
            st.warning("""
            No articles found. Try:
            - Different tickers
            - More data sources
            - A longer time period
            """)

if __name__ == "__main__":
    main()