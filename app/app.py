import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Optional
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import io

# Configuration Class
class Config:
    def __init__(self):
        self.CACHE_TTL = 3600  # 1 hour cache
        self.API_KEYS = {
            'alpha_vantage': '01DTV6BVSWVIZSX2',
            'newsapi': 'bbf76eb5888b480d8d910a091c56ec3d',
            'finnhub': 'd09r1p9r01qus8rest20d09r1p9r01qus8rest2g'
        }
        self.TOPICS = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'IBM'],
            'Finance': ['JPM', 'BAC', 'GS', 'MS', 'C'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
            'Cryptocurrency': ['BTC', 'ETH', 'ADA', 'DOGE'],
            'Forex': ['USD', 'EUR', 'GBP', 'JPY']
        }
        self.SOURCES = [
            'Bloomberg', 'Reuters', 'CNBC', 
            'Wall Street Journal', 'Financial Times'
        ]
        self.API_ENDPOINTS = {
            'finnhub': 'https://finnhub.io/api/v1/stock/symbol?exchange=US',
            'alpha_vantage': 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM',
            'newsapi': 'https://newsapi.org/v2/top-headlines?country=us'
        }

# Sentiment Analyzer Class
class SentimentAnalyzer:
    def __init__(self):
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
            df['text'] = df.get('description', df.get('summary', ''))
        
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
class FinnhubFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        
    def fetch_news(self, tickers: List[str], days_back: int = 7) -> pd.DataFrame:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            response = requests.get(
                f"{self.base_url}/news?category=general&token={self.api_key}"
            )
            response.raise_for_status()
            data = response.json()
             
            if not data:
                st.warning("No news articles found from Finnhub")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            
            # Process the data
            df['published'] = pd.to_datetime(df['datetime'], unit='s')
            df['source'] = df['source'].fillna('Unknown')
            df['title'] = df.get('headline', '')
            df['text'] = df.get('summary', '')
            df['url'] = df.get('url', '')
            df['image'] = df.get('image', '')
            
            # Initialize empty list column for tickers
            df['tickers'] = [[] for _ in range(len(df))]
            
             
            # Filter by tickers if provided
            if tickers:
                tickers_lower = [t.lower() for t in tickers]
                
                for i, row in df.iterrows():
                    content = (row['title'] + ' ' + row['text']).lower()
                    matched_tickers = [
                        tickers[i] for i, t in enumerate(tickers_lower) 
                        if t in content
                    ]
                    df.at[i, 'tickers'] = matched_tickers
                
                # Remove rows with no matching tickers
                #df = df[df['tickers'].apply(len) > 0]
            
            # Filter by date
            df = df[(df['published'] >= start_date) & (df['published'] <= end_date)]
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"Finnhub API Request Failed: {str(e)}")
            return pd.DataFrame()

class AlphaVantageFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
    def fetch_news(self, tickers: List[str], start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        try:
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": self.api_key,
                "limit": "200"
            }
            
            if tickers:
                params["tickers"] = ",".join(tickers)
            
            if start_date and end_date:
                params["time_from"] = start_date.strftime("%Y%m%dT%H%M")
                params["time_to"] = end_date.strftime("%Y%m%dT%H%M")
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Note" in data and "API call frequency" in data["Note"]:
                st.warning("Alpha Vantage API rate limit reached")
                return pd.DataFrame()
                
            if "feed" not in data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data["feed"])
            
            if df.empty:
                return df
                
            df['published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S')
            df['source'] = df['source'].str.replace('^.*\\|\\s*', '', regex=True)
            df['title'] = df.get('title', '')
            df['text'] = df.get('summary', '')
            df['url'] = df.get('url', '')
            df['image'] = df.get('banner_image', '')
            df['tickers'] = df['ticker_sentiment'].apply(
                lambda x: [item['ticker'] for item in x] if isinstance(x, list) else []
            )
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"Alpha Vantage API Request Failed: {str(e)}")
            return pd.DataFrame()

# In the NewsAPIFetcher class, modify the fetch_news method:
class NewsAPIFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_news(self, tickers: List[str], days_back: int) -> pd.DataFrame:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            query = " OR ".join([f"${t}" for t in tickers])
            params = {
                "q": query,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "language": "en",
                "sortBy": "publishedAt",
                "apiKey": self.api_key,
                "pageSize": 100
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                st.error(f"NewsAPI Error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
                
            df = pd.DataFrame(data["articles"])
            
            if df.empty:
                return df
                
            df['published'] = pd.to_datetime(df['publishedAt'])
            df['source'] = df['source'].apply(lambda x: x.get('name', 'Unknown'))
            
            # Handle potential NaN/float values in text fields
            df['title'] = df.get('title', '').apply(lambda x: str(x) if pd.notna(x) else '')
            df['description'] = df.get('description', '').apply(lambda x: str(x) if pd.notna(x) else '')
            df['content'] = df.get('content', '').apply(lambda x: str(x) if pd.notna(x) else '')
            
            df['text'] = (df['description'] + " " + df['content']).str.strip()
            df['url'] = df.get('url', '')
            df['image'] = df.get('urlToImage', '')
            
            # Initialize tickers column
            df['tickers'] = [[] for _ in range(len(df))]
            
            # Find matching tickers
            if tickers:
                tickers_lower = [t.lower() for t in tickers]
                for i, row in df.iterrows():
                    # Safely handle text concatenation
                    title = str(row['title']) if pd.notna(row['title']) else ''
                    text = str(row['text']) if pd.notna(row['text']) else ''
                    content = (title + ' ' + text).lower()
                    
                    matched_tickers = [
                        tickers[i] for i, t in enumerate(tickers_lower) 
                        if f"${t}" in content or t in content
                    ]
                    df.at[i, 'tickers'] = matched_tickers
                
                df = df[df['tickers'].apply(len) > 0]
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"NewsAPI Request Failed: {e}")
            return pd.DataFrame()
        
# Add this new function
def check_api_status(config: Config) -> Dict[str, bool]:
    """Check status of all APIs"""
    status = {}
    try:
        # Check Finnhub
        finnhub_res = requests.get(
            config.API_ENDPOINTS['finnhub'],
            params={"token": config.API_KEYS['finnhub']}
        )
        status['finnhub'] = finnhub_res.status_code == 200
        
        # Check Alpha Vantage
        alpha_res = requests.get(
            config.API_ENDPOINTS['alpha_vantage'],
            params={"apikey": config.API_KEYS['alpha_vantage']}
        )
        status['alpha_vantage'] = alpha_res.status_code == 200
        
        # Check NewsAPI
        newsapi_res = requests.get(
            config.API_ENDPOINTS['newsapi'],
            params={"apiKey": config.API_KEYS['newsapi']}
        )
        status['newsapi'] = newsapi_res.status_code == 200
        
    except requests.exceptions.RequestException:
        status = {api: False for api in config.API_KEYS.keys()}
    
    return status

def show_sidebar(config: Config):
    with st.sidebar:
        st.header("API Status")
        
        # Get API status
        api_status = check_api_status(config)
        
        # Display status indicators
        #col1, col2, col3 = st.columns(3)
        #with col1:
        st.markdown(f"**Finnhub**: {'🟢 Online' if api_status['finnhub'] else '🔴'}")
        #with col2:
        st.markdown(f"**Alpha Vantage**: {'🟢Online' if api_status['alpha_vantage'] else '🔴'}")
        #with col3:
        st.markdown(f"**NewsAPI**: {'🟢Online' if api_status['newsapi'] else '🔴'}")
        
        # Add usage warning if any API is down
        if not all(api_status.values()):
            st.warning("Some APIs are unavailable. Features may be limited.")
            st.markdown("**API:** 🔴 Offline")
        
 
        st.header("Analysis Settings")
        
        # API status check
        #try:
        #    test_finnhub = requests.get(f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={config.API_KEYS['finnhub']}")
        #    status = "🟢 Online" if test_finnhub.status_code == 200 else "🟠 Limited"
        #    st.markdown(f"**Finnhub API:** {status}")
        #    st.markdown(f"**Alpha Vantage**: {'🟢 Online' if api_status['alpha_vantage'] else '🔴'}")
        #    st.markdown(f"**NewsAPI**: {'🟢Online' if api_status['newsapi'] else '🔴'}")
            
        #except:
        #    st.markdown("**Finnhub API:** 🔴 Offline")
        
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
            default=config.TOPICS[selected_topic][:3]
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
            ["Finnhub", "Alpha Vantage API", "NewsAPI", "Local CSV File"],
            index=0
        )
        
        # Debug mode
        debug_mode = st.checkbox("Enable Debug Mode")
        
        return selected_tickers, selected_sources, days_back, min_sentiment, data_source, debug_mode

def show_news_swiper(df: pd.DataFrame):
    if df.empty or 'url' not in df.columns or 'title' not in df.columns:
        return
    
    st.subheader("📰 News Swiper")
    
    if 'index' not in st.session_state:
        st.session_state.index = 0
    
    if st.session_state.index >= len(df):
        st.session_state.index = 0
    
    article = df.iloc[st.session_state.index]
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if 'image' in article and pd.notna(article['image']) and article['image'] != '':
            st.image(article['image'], caption=f"Source: {article.get('source', 'Unknown')}", width=300)
        
        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            if st.button("⏮️ Previous") and st.session_state.index > 0:
                st.session_state.index -= 1
                st.rerun()
        with nav_col2:
            if st.button("⏭️ Next") and st.session_state.index < len(df) - 1:
                st.session_state.index += 1
                st.rerun()
    
    with col2:
        st.subheader(article['title'])
        
        sentiment = article.get('vader_compound', 0)
        sentiment_color = "green" if sentiment >= 0.05 else ("red" if sentiment <= -0.05 else "gray")
        st.markdown(f"**Sentiment:** :{sentiment_color}[{sentiment:.2f}]")
        
        if 'text' in article and pd.notna(article['text']):
            st.markdown(article['text'][:500] + "...")
        
        meta_col1, meta_col2 = st.columns([1, 1])
        with meta_col1:
            if 'published' in article:
                st.caption(f"📅 {article['published'].strftime('%Y-%m-%d %H:%M')}")
        with meta_col2:
            if 'tickers' in article:
                tickers = ", ".join(article['tickers']) if article['tickers'] else "None"
                st.caption(f"📊 Tickers: {tickers}")
        
        st.markdown(f"[Read full article ↗️]({article['url']})")

def show_sentiment_analysis(df: pd.DataFrame):
    st.subheader("Sentiment Over Time")
    
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
    st.plotly_chart(fig1, use_container_width=True)
    
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
    st.subheader("Ticker Sentiment Comparison")
    
    if df.empty or 'tickers' not in df.columns:
        st.warning("No ticker data available")
        return
    
    try:
        exploded_df = df.explode('tickers')
        exploded_df = exploded_df[exploded_df['tickers'].notna()]
        
        if exploded_df.empty:
            st.warning("No valid ticker references found")
            return
        
        ticker_sentiment = exploded_df.groupby('tickers', observed=True).agg(
            mean_sentiment=('vader_compound', 'mean'),
            article_count=('title', 'count')
        ).sort_values('mean_sentiment')
        
        if ticker_sentiment.empty:
            st.warning("No ticker sentiment data available")
            return
            
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
        
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_categoryorder='total ascending'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating ticker comparison: {str(e)}")

def show_source_analysis(df: pd.DataFrame):
    st.subheader("Source Analysis")
    
    if df.empty or 'source' not in df.columns:
        st.warning("No source data available")
        return
    
    credibility_scores = {
        'Bloomberg': 9.5,
        'Reuters': 9.5,
        'CNBC': 8.5,
        'Wall Street Journal': 9.0,
        'Financial Times': 9.0
    }
    
    df['credibility'] = df['source'].map(credibility_scores).fillna(7.0)
    
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
    st.subheader("Article Data")
    
    if df.empty:
        st.warning("No data available")
        return
    
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
    
    filtered_df = df[
        (df['vader_compound'] >= min_sentiment) &
        (df['source'].isin(selected_sources if selected_sources else df['source'].unique()))
    ].sort_values('published', ascending=False)
    
    if filtered_df.empty:
        st.warning("No articles match your filters")
        return
    
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
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output.getvalue()

@st.cache_data(ttl=3600)
def fetch_data_from_csv(uploaded_file, days_back=7):
    try:
        df = pd.read_csv(uploaded_file)
        
        if 'published' in df.columns:
            df['published'] = pd.to_datetime(df['published'])
        elif 'publishedAt' in df.columns:
            df['published'] = pd.to_datetime(df['publishedAt'])
        else:
            st.error("CSV must contain 'published' or 'publishedAt' column")
            return pd.DataFrame()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        df = df[(df['published'] >= start_date) & (df['published'] <= end_date)]
        
        if 'title' not in df.columns:
            df['title'] = ''
        if 'text' not in df.columns:
            df['text'] = df.get('description', df.get('summary', ''))
        if 'source' not in df.columns:
            df['source'] = 'Unknown'
        if 'url' not in df.columns:
            df['url'] = ''
        if 'tickers' not in df.columns:
            df['tickers'] = [[] for _ in range(len(df))]
        
        return df
    
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()

def show_main_content(df: pd.DataFrame, min_sentiment: float):
    if df.empty:
        st.warning("No news articles match your filters")
        return
    
    df = df[df['vader_compound'] >= min_sentiment]
    
    if df.empty:
        st.warning("No articles meet the minimum sentiment threshold")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    avg_sentiment = df['vader_compound'].mean()
    col1.metric("Average Sentiment", f"{avg_sentiment:.2f}", 
               "Positive" if avg_sentiment > 0 else "Negative")
    col2.metric("Total Articles", len(df))
    col3.metric("Sources", df['source'].nunique())
    col4.metric("Tickers Covered", df['tickers'].explode().nunique())
    
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
    
    st.divider()
    st.subheader("Export Data")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        csv = convert_df_to_csv(filtered_df if 'filtered_df' in locals() else df)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="financial_news_sentiment.csv",
            mime="text/csv",
            help="Download the current view of the data (with filters applied)"
        )
    
    with col2:
        st.info("The downloaded CSV will contain all available fields including sentiment scores.")

def main():
    config = Config()
    analyzer = SentimentAnalyzer()
    
    st.set_page_config(
        page_title="Financial News Sentiment Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📰 Financial News Sentiment Dashboard")
    
    (selected_tickers, selected_sources, days_back, 
     min_sentiment, data_source, debug_mode) = show_sidebar(config)
    
    analyzed_df = pd.DataFrame()
    
    if data_source == "Finnhub":
        if not selected_tickers:
            st.warning("Please select at least one ticker")
            return
        
        with st.spinner("Fetching news from Finnhub..."):
            fetcher = FinnhubFetcher(config.API_KEYS['finnhub'])
            news_df = fetcher.fetch_news(selected_tickers, days_back)
            #print(news_df)   # Debugging line
            if not news_df.empty:
                if selected_sources and 'source' in news_df.columns:
                    news_df = news_df[news_df['source'].isin(selected_sources)]
                analyzed_df = analyzer.analyze_dataframe(news_df)
            else:
                st.error("No news articles found from Finnhub. Try different tickers.")
                return
    
    elif data_source == "Alpha Vantage API":
        if not selected_tickers:
            st.warning("Please select at least one ticker")
            return
        
        with st.spinner("Fetching news from Alpha Vantage..."):
            fetcher = AlphaVantageFetcher(config.API_KEYS['alpha_vantage'])
            start_date = datetime.now() - timedelta(days=days_back)
            end_date = datetime.now()
            news_df = fetcher.fetch_news(selected_tickers, start_date, end_date)
            
            if news_df.empty:
                st.warning("Trying without date filter...")
                news_df = fetcher.fetch_news(selected_tickers, None, None)
            
            if not news_df.empty:
                if selected_sources and 'source' in news_df.columns:
                    news_df = news_df[news_df['source'].isin(selected_sources)]
                analyzed_df = analyzer.analyze_dataframe(news_df)
            else:
                st.error("No news found from Alpha Vantage. Check rate limits.")
                return
    
    elif data_source == "NewsAPI":
        if not selected_tickers:
            st.warning("Please select at least one ticker")
            return
        
        with st.spinner("Fetching news from NewsAPI..."):
            fetcher = NewsAPIFetcher(config.API_KEYS['newsapi'])
            news_df = fetcher.fetch_news(selected_tickers, days_back)
            
            if not news_df.empty:
                if selected_sources and 'source' in news_df.columns:
                    news_df = news_df[news_df['source'].isin(selected_sources)]
                analyzed_df = analyzer.analyze_dataframe(news_df)
            else:
                st.error("No news found from NewsAPI. Check rate limits.")
                return
    
    else:  # Local CSV
        uploaded_file = st.sidebar.file_uploader(
            "Upload a CSV file", 
            type="csv",
            help="CSV should contain news articles with columns like title, source, published date, etc."
        )
        
        if uploaded_file is not None:
            with st.spinner("Processing uploaded CSV..."):
                news_df = fetch_data_from_csv(uploaded_file, days_back)
                
                if not news_df.empty:
                    if selected_sources and 'source' in news_df.columns:
                        news_df = news_df[news_df['source'].isin(selected_sources)]
                    analyzed_df = analyzer.analyze_dataframe(news_df)
                else:
                    st.error("No valid data found in the uploaded CSV file.")
                    return
        else:
            st.info("Please upload a CSV file containing news data.")
            return
    
    if debug_mode and not analyzed_df.empty:
        st.subheader("Debug Information")
        st.json({
            "data_shape": analyzed_df.shape,
            "columns": list(analyzed_df.columns),
            "sample_row": analyzed_df.iloc[0].to_dict(),
            "missing_values": analyzed_df.isnull().sum().to_dict()
        })
    
    show_news_swiper(analyzed_df)
    show_main_content(analyzed_df, min_sentiment)

if __name__ == "__main__":
    main()