import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Optional
import numpy as np

# Configuration Class
class Config:
    def __init__(self):
        self.CACHE_TTL = 3600  # 1 hour cache
        self.API_KEYS = {
            'alpha_vantage': '01DTV6BVSWVIZSX2',
            'newsapi': 'bbf76eb5888b480d8d910a091c56ec3d'
        }
        self.TOPICS = {
            'Technology': ['IBM','AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
            'Finance': ['JPM', 'BAC', 'GS', 'MS', 'C'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
            'Cryptocurrency': ['CRYPTO:BTC', 'CRYPTO:ETH', 'CRYPTO:ADA', 'CRYPTO:DOGE'],
            'Forex': ['FOREX:USD', 'FOREX:EUR', 'FOREX:GBP', 'FOREX:JPY']
        }
        self.SOURCES = [
            'Zacks Commentary','Motley Fool','Bloomberg', 'Reuters', 'CNBC', 
            'Wall Street Journal','Benzinga', 'Financial Times', 'MarketWatch', 'Seeking Alpha'
        ]

# Sentiment Analyzer Class
class SentimentAnalyzer:
    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> dict:
        if not text or pd.isna(text):
            return {'compound': 0.0, 'neg': 0.0, 'neu': 0.0, 'pos': 0.0}
        return self.analyzer.polarity_scores(text)
    
    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Ensure required columns exist
        if 'title' not in df.columns:
            df['title'] = ''
        if 'text' not in df.columns:
            df['text'] = df.get('description', '')
        
        # Analyze sentiment
        df['sentiment'] = df.apply(
            lambda row: self.analyze_text(f"{row['title']}. {row['text']}"), 
            axis=1
        )
        
        # Expand sentiment scores
        df['vader_compound'] = df['sentiment'].apply(lambda x: x['compound'])
        df['vader_neg'] = df['sentiment'].apply(lambda x: x['neg'])
        df['vader_neu'] = df['sentiment'].apply(lambda x: x['neu'])
        df['vader_pos'] = df['sentiment'].apply(lambda x: x['pos'])
        
        # Add sentiment label
        df['sentiment_label'] = df['vader_compound'].apply(
            lambda x: 'positive' if x >= 0.05 else ('negative' if x <= -0.05 else 'neutral')
        )
        
        return df

# News Fetcher Classes
class AlphaVantageFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
    def fetch_news(self, tickers: List[str], start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        try:
            # Separate ticker types
            regular_tickers = [t for t in tickers if not (t.startswith('CRYPTO:') or t.startswith('FOREX:'))]
            crypto_tickers = [t.replace('CRYPTO:', '') for t in tickers if t.startswith('CRYPTO:')]
            forex_tickers = [t.replace('FOREX:', '') for t in tickers if t.startswith('FOREX:')]
            
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": self.api_key,
                "limit": "200"  # Increased limit
            }
            
            # Add tickers if we have regular ones
            if regular_tickers:
                params["tickers"] = ",".join(regular_tickers)
            
            # Add topics for crypto/forex
            topics = []
            if crypto_tickers:
                topics.append("blockchain")
            if forex_tickers:
                topics.append("forex_market")
            if topics:
                params["topics"] = ",".join(topics)
            
            # Add time range if specified
            if start_date and end_date:
                params["time_from"] = start_date.strftime("%Y%m%dT%H%M")
                params["time_to"] = end_date.strftime("%Y%m%dT%H%M")
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for rate limit message
            if "Note" in data and "API call frequency" in data["Note"]:
                st.warning("API rate limit reached. Please wait a minute or upgrade your plan.")
                return pd.DataFrame()
            
            if "feed" not in data:
                st.warning(f"No news articles found for: {tickers}")
                return pd.DataFrame()
                
            df = pd.DataFrame(data["feed"])
            
            if df.empty:
                return df
                
            # Process the data
            df['published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S')
            df['tickers'] = df['ticker_sentiment'].apply(
                lambda x: [item['ticker'] for item in x] if isinstance(x, list) else []
            )
            
            # Add crypto/forex tickers to relevant articles
            additional_tickers = crypto_tickers + forex_tickers
            if additional_tickers:
                df['tickers'] = df['tickers'].apply(
                    lambda x: x + additional_tickers if x else additional_tickers
                )
            
            df['source'] = df['source'].str.replace('^.*\\|\\s*', '', regex=True)
            df['title'] = df.get('title', '')
            df['text'] = df.get('summary', '')
            df['url'] = df.get('url', '')
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Request Failed: {str(e)}")
            return pd.DataFrame()

class NewsAPIFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_news(self, tickers: List[str], days_back: int) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = " OR ".join([f"${ticker}" for ticker in tickers if not (ticker.startswith('CRYPTO:') or ticker.startswith('FOREX:'))])
        
        params = {
            "q": query,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.api_key,
            "pageSize": 100  # Max allowed by free tier
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                st.error(f"NewsAPI Error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
                
            df = pd.DataFrame(data["articles"])
            
            if df.empty:
                return df
                
            # Process the data
            df['published'] = pd.to_datetime(df['publishedAt'])
            df['source'] = df['source'].apply(lambda x: x.get('name', 'Unknown'))
            df['tickers'] = df.apply(
                lambda row: [ticker for ticker in tickers if ticker.lower() in row['title'].lower()], 
                axis=1
            )
            df['text'] = df.get('description', '') + " " + df.get('content', '')
            df['url'] = df.get('url', '')
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"NewsAPI Request Failed: {e}")
            return pd.DataFrame()

def check_alpha_vantage_status(api_key: str) -> bool:
    """Check if Alpha Vantage API is working"""
    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": "AAPL",
            "apikey": api_key,
            #"limit": "1"
        }
        response = requests.get("https://www.alphavantage.co/query", params=params)
        print(response.json())
        print(f"https://www.alphavantage.co/query",  {params})
        data = response.json()
        return "feed" in data
    except:
        return False

# Streamlit UI Components
def show_sidebar(config: Config):
    """Render the sidebar controls"""
    with st.sidebar:
        # API status indicator
        if check_alpha_vantage_status(config.API_KEYS['alpha_vantage']):
            st.success("Alpha Vantage API: Online")
        else:
            st.error("Alpha Vantage API: Offline (check key or limits)")
        
        st.header("Analysis Settings")
        
        # Topic selection
        selected_topic = st.selectbox(
            "Select Market Sector",
            options=list(config.TOPICS.keys()),
            index=0
        )
        
        # Ticker selection
        selected_tickers = st.multiselect(
            "Select Tickers",
            options=config.TOPICS[selected_topic],
            default=config.TOPICS[selected_topic][:3],
            help="For cryptocurrencies use CRYPTO:BTC format, for forex use FOREX:USD"
        )
        
        # Source filtering
        selected_sources = st.multiselect(
            "Filter by Sources",
            options=config.SOURCES,
            default=config.SOURCES[:3]
        )
        
        # Time period
        days_back = st.slider("Analysis Period (Days)", 1, 30, 7)
        
        # Sentiment filter
        min_sentiment = st.slider(
            "Minimum Sentiment Score",
            -1.0, 1.0, -1.0
        )
        
        # Data source selection
        data_source = st.radio(
            "Select Data Source",
            ["Alpha Vantage API", "NewsAPI", "Local CSV File"],
            index=0
        )
        
        # Debug mode
        debug_mode = st.checkbox("Enable Debug Mode")
        
        return selected_tickers, selected_sources, days_back, min_sentiment, data_source, debug_mode

def show_news_swiper(df: pd.DataFrame):
    """Display news articles in a swiper format"""
    if df.empty or 'url' not in df.columns or 'title' not in df.columns:
        return
    
    st.subheader("📰 News Swiper")
    
    # Track the index of the article being displayed
    if 'index' not in st.session_state:
        st.session_state.index = 0
    
    # Reset index if it's out of bounds
    if st.session_state.index >= len(df):
        st.session_state.index = 0
    
    # Display current article
    article = df.iloc[st.session_state.index]
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display image if available
        if 'urlToImage' in article and pd.notna(article['urlToImage']):
            st.image(article['urlToImage'], caption=f"Source: {article.get('source', 'Unknown')}", width=300)
        
        # Navigation buttons
        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            if st.button("⏮️ Previous") and st.session_state.index > 0:
                st.session_state.index -= 1
                st.experimental_rerun()
        with nav_col2:
            if st.button("⏭️ Next") and st.session_state.index < len(df) - 1:
                st.session_state.index += 1
                st.experimental_rerun()
    
    with col2:
        st.subheader(article['title'])
        
        # Display sentiment
        sentiment = article.get('vader_compound', 0)
        sentiment_color = "green" if sentiment >= 0.05 else ("red" if sentiment <= -0.05 else "gray")
        st.markdown(f"**Sentiment:** :{sentiment_color}[{sentiment:.2f}]")
        
        # Display article content
        if 'text' in article and pd.notna(article['text']):
            st.markdown(article['text'][:500] + "...")  # Show first 500 chars
        
        # Display metadata
        meta_col1, meta_col2 = st.columns([1, 1])
        with meta_col1:
            if 'published' in article:
                st.caption(f"📅 {article['published'].strftime('%Y-%m-%d %H:%M')}")
        with meta_col2:
            if 'tickers' in article:
                tickers = ", ".join([t.replace('CRYPTO:', '').replace('FOREX:', '') for t in article['tickers']]) if article['tickers'] else "None"
                st.caption(f"📊 Tickers: {tickers}")
        
        st.markdown(f"[Read full article ↗️]({article['url']})")

def show_sentiment_analysis(df: pd.DataFrame):
    """Sentiment trends and distributions"""
    st.subheader("Sentiment Over Time")
    
    # Prepare time series data
    df['date'] = pd.to_datetime(df['published']).dt.date
    daily_sentiment = df.groupby(['date', 'sentiment_label']).size().unstack().fillna(0)
    
    # Create visualization
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
    st.plotly_chart(fig1, use_container_width=True)
    
    # Sentiment distribution
    st.subheader("Sentiment Distribution")
    fig2 = px.histogram(
        df,
        x='vader_compound',
        nbins=20,
        title="Sentiment Score Distribution",
        labels={'vader_compound': 'Sentiment Score'},
        color='sentiment_label',
        color_discrete_map={
            'positive': '#2ecc71',
            'neutral': '#f1c40f',
            'negative': '#e74c3c'
        }
    )
    st.plotly_chart(fig2, use_container_width=True)

def show_ticker_comparison(df: pd.DataFrame):
    """Compare sentiment across tickers"""
    st.subheader("Ticker Sentiment Comparison")
    
    if df.empty or 'tickers' not in df.columns:
        st.warning("No ticker data available")
        return
    
    try:
        # Explode the tickers lists into separate rows
        exploded_df = df.explode('tickers')
        exploded_df = exploded_df[exploded_df['tickers'].notna()]
        
        if exploded_df.empty:
            st.warning("No valid ticker references found in articles")
            return
        
        # Calculate average sentiment per ticker
        ticker_sentiment = exploded_df.groupby('tickers', observed=True).agg(
            mean_sentiment=('vader_compound', 'mean'),
            article_count=('title', 'count')
        ).sort_values('mean_sentiment')
        
        if ticker_sentiment.empty:
            st.warning("No ticker sentiment data available")
            return
            
        # Create visualization with better formatting for crypto/forex
        fig = px.bar(
            ticker_sentiment,
            x='mean_sentiment',
            y=ticker_sentiment.index,
            orientation='h',
            color='mean_sentiment',
            color_continuous_scale='RdYlGn',
            title="Average Sentiment by Ticker",
            labels={'mean_sentiment': 'Sentiment Score', 'index': 'Ticker'},
            hover_data=['article_count']
        )
        
        # Improve y-axis labels for crypto/forex
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=ticker_sentiment.index,
                ticktext=[t.replace('CRYPTO:', '').replace('FOREX:', '') for t in ticker_sentiment.index]
            ),
            coloraxis_showscale=False,
            yaxis_categoryorder='total ascending'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating ticker comparison: {str(e)}")

def show_source_analysis(df: pd.DataFrame):
    """Analyze news sources"""
    st.subheader("Source Analysis")
    
    if df.empty or 'source' not in df.columns:
        st.warning("No source data available")
        return
    
    # Source credibility scoring
    credibility_scores = {
        'Zacks Commentary': 8.0,
        'Motley Fool': 8.0,
        'Bloomberg': 9.5,
        'Reuters': 9.5,
        'CNBC': 8.5,
        'Wall Street Journal': 9.0,
        'Benzinga': 7.5,
        'Financial Times': 9.0,
        'MarketWatch': 8.0,
        'Seeking Alpha': 7.5
    }
    
    # Add credibility to dataframe
    df['credibility'] = df['source'].map(credibility_scores).fillna(7.0)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Source Distribution", "Source Credibility"])
    
    with tab1:
        source_counts = df['source'].value_counts().nlargest(10)
        if not source_counts.empty:
            fig1 = px.pie(
                source_counts,
                names=source_counts.index,
                values=source_counts.values,
                title="Top News Sources"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No source distribution data available")
    
    with tab2:
        source_stats = df.groupby('source').agg({
            'vader_compound': 'mean',
            'credibility': 'first'
        }).sort_values('credibility', ascending=False)
        
        if not source_stats.empty:
            fig2 = px.bar(
                source_stats,
                x='vader_compound',
                y=source_stats.index,
                color='credibility',
                title="Average Sentiment by Source (Colored by Credibility)",
                labels={'vader_compound': 'Avg. Sentiment', 'y': 'Source'},
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No source sentiment data available")

def show_raw_data(df: pd.DataFrame):
    """Display raw data with filtering options"""
    st.subheader("Article Data")
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Add filtering options
    col1, col2 = st.columns(2)
    with col1:
        min_sentiment = st.slider(
            "Filter by Minimum Sentiment",
            -1.0, 1.0, -1.0,
            key="raw_data_sentiment"
        )
    with col2:
        selected_sources = st.multiselect(
            "Filter by Sources",
            options=df['source'].unique(),
            default=df['source'].unique()[:3],
            key="raw_data_sources"
        )
    
    # Apply filters
    filtered_df = df[
        (df['vader_compound'] >= min_sentiment) &
        (df['source'].isin(selected_sources if selected_sources else df['source'].unique()))
    ].sort_values('published', ascending=False)
    
    if filtered_df.empty:
        st.warning("No articles match your filters")
        return
    
    # Display data
    st.dataframe(
        filtered_df[['title', 'source', 'published', 'tickers', 'vader_compound', 'sentiment_label']],
        column_config={
            "title": "Headline",
            "source": "Source",
            "published": "Date",
            "tickers": "Tickers",
            "vader_compound": st.column_config.NumberColumn(
                "Sentiment",
                format="%.2f",
                help="VADER compound sentiment score (-1 to 1)"
            ),
            "sentiment_label": "Label"
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )
    
    return filtered_df

def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Convert dataframe to CSV bytes for download"""
    import io
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output.getvalue()

@st.cache_data(ttl=3600)
def fetch_data_from_csv(uploaded_file, days_back=7):
    """Fetch stock data from a CSV file"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Handle different CSV formats
        if 'published' in df.columns:
            df['published'] = pd.to_datetime(df['published'])
        elif 'publishedAt' in df.columns:
            df['published'] = pd.to_datetime(df['publishedAt'])
        else:
            st.error("CSV must contain 'published' or 'publishedAt' column")
            return pd.DataFrame()
        
        # Filter by date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        df = df[(df['published'] >= start_date) & (df['published'] <= end_date)]
        
        # Ensure required columns
        if 'title' not in df.columns:
            df['title'] = ''
        if 'text' not in df.columns:
            df['text'] = df.get('description', '') + " " + df.get('content', '')
        if 'source' not in df.columns:
            df['source'] = 'Unknown'
        if 'url' not in df.columns:
            df['url'] = ''
        if 'tickers' not in df.columns:
            df['tickers'] = [[]] * len(df)
        
        return df
    
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()

def show_main_content(df: pd.DataFrame, min_sentiment: float):
    """Render the main dashboard content"""
    if df.empty:
        st.warning("No news articles match your filters")
        return
    
    # Filter by sentiment
    df = df[df['vader_compound'] >= min_sentiment]
    
    if df.empty:
        st.warning("No articles meet the minimum sentiment threshold")
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    avg_sentiment = df['vader_compound'].mean()
    sentiment_diff = abs(avg_sentiment - min_sentiment)
    col1.metric(
        "Average Sentiment", 
        f"{avg_sentiment:.2f}", 
        "Positive" if avg_sentiment > 0 else "Negative"
    )
    col2.metric("Total Articles", len(df))
    col3.metric("Sources", df['source'].nunique())
    col4.metric("Tickers Covered", df['tickers'].explode().nunique())
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Sentiment Analysis", 
        "🏷️ Ticker Comparison", 
        "📰 Source Insights", 
        "📋 Raw Data"
    ])
    
    with tab1:
        show_sentiment_analysis(df)
    
    with tab2:
        show_ticker_comparison(df)
    
    with tab3:
        show_source_analysis(df)
    
    with tab4:
        filtered_df = show_raw_data(df)
    
    # Add download button at the bottom of the main content
    st.divider()
    st.subheader("Export Data")
    
    # Prepare columns for better layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Button to download the filtered data
        csv = convert_df_to_csv(filtered_df if 'filtered_df' in locals() else df)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="financial_news_sentiment.csv",
            mime="text/csv",
            help="Download the current view of the data (with filters applied)"
        )
    
    with col2:
        st.info("The downloaded CSV will contain all available fields including sentiment scores, source information, and article text.")

def main():
    """Main application function"""
    # Initialize configuration
    config = Config()
    analyzer = SentimentAnalyzer()
    
    # Set up page configuration
    st.set_page_config(
        page_title="Financial News Sentiment Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📰 Financial News Sentiment Dashboard")
    
    # Get user inputs from sidebar
    (selected_tickers, selected_sources, days_back, 
     min_sentiment, data_source, debug_mode) = show_sidebar(config)
    
    # Initialize dataframe
    analyzed_df = pd.DataFrame()
    
    # Fetch data based on selected source
    if data_source in ["Alpha Vantage API", "NewsAPI"]:
        if not selected_tickers:
            st.warning("Please select at least one ticker")
            return
        
        with st.spinner("Fetching and analyzing news..."):
            if data_source == "Alpha Vantage API":
                fetcher = AlphaVantageFetcher(config.API_KEYS['alpha_vantage'])
                start_date = datetime.now() - timedelta(days=days_back)
                end_date = datetime.now()
                news_df = fetcher.fetch_news(selected_tickers, start_date, end_date)
                
                # If no data, try without date filter
                if news_df.empty:
                    st.warning("Trying without date filter...")
                    news_df = fetcher.fetch_news(selected_tickers, None, None)
            else:  # NewsAPI
                fetcher = NewsAPIFetcher(config.API_KEYS['newsapi'])
                news_df = fetcher.fetch_news(selected_tickers, days_back)
            
            if not news_df.empty:
                # Apply source filtering if sources are selected
                if selected_sources and 'source' in news_df.columns:
                    news_df = news_df[news_df['source'].isin(selected_sources)]
                
                # Analyze sentiment
                analyzed_df = analyzer.analyze_dataframe(news_df)
            else:
                st.error("""
                No news articles found. Possible solutions:
                1. Try different tickers or time period
                2. Check your API key limits
                3. Some tickers may not have recent news coverage
                """)
                
                # Show sample data option
                if st.checkbox("Show sample data for demo"):
                    sample_data = {
                        'title': ["Sample: Bitcoin reaches new high", "Sample: Fed raises interest rates"],
                        'source': ["CryptoNews", "Financial Times"],
                        'published': [datetime.now(), datetime.now() - timedelta(days=1)],
                        'tickers': [[selected_tickers[0] if selected_tickers else "AAPL"], 
                                   [selected_tickers[0] if selected_tickers else "AAPL"]],
                        'url': ["https://example.com/1", "https://example.com/2"],
                        'text': [
                            "Bitcoin reached a new all-time high amid institutional adoption.",
                            "Federal Reserve announced a 0.25% interest rate hike to combat inflation."
                        ]
                    }
                    news_df = pd.DataFrame(sample_data)
                    analyzed_df = analyzer.analyze_dataframe(news_df)
                else:
                    return
    else:  # Local CSV File
        uploaded_file = st.sidebar.file_uploader(
            "Upload a CSV file", 
            type="csv",
            help="CSV should contain news articles with columns like title, source, published date, etc."
        )
        
        if uploaded_file is not None:
            with st.spinner("Processing uploaded CSV..."):
                news_df = fetch_data_from_csv(uploaded_file, days_back)
                
                if not news_df.empty:
                    # Apply source filtering if sources are selected and column exists
                    if selected_sources and 'source' in news_df.columns:
                        news_df = news_df[news_df['source'].isin(selected_sources)]
                    
                    # Analyze sentiment
                    analyzed_df = analyzer.analyze_dataframe(news_df)
                else:
                    st.error("No valid data found in the uploaded CSV file.")
                    return
        else:
            st.info("Please upload a CSV file containing news data.")
            return
    
    # Debug information
    if debug_mode and not analyzed_df.empty:
        st.subheader("Debug Information")
        st.json({
            "data_shape": analyzed_df.shape,
            "columns": list(analyzed_df.columns),
            "sample_row": analyzed_df.iloc[0].to_dict(),
            "missing_values": analyzed_df.isnull().sum().to_dict()
        })
    
    # Display news swiper
    show_news_swiper(analyzed_df)
    
    # Show main content with sentiment analysis
    show_main_content(analyzed_df, min_sentiment)

if __name__ == "__main__":
    main()