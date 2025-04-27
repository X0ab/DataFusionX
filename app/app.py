import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from news_fetchers.alpha_vantage import AlphaVantageFetcher
from analyzers.sentiment_analyzer import SentimentAnalyzer
from config.settings import Config
import numpy as np

# Initialize configuration
config = Config()
analyzer = SentimentAnalyzer()

# Set up page configuration
st.set_page_config(
    page_title="Financial News Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=config.CACHE_TTL)
def fetch_data(tickers, days_back):
    """Fetch news data with caching"""
    fetcher = AlphaVantageFetcher(config.API_KEYS['alpha_vantage'])
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return fetcher.fetch_news(tickers, start_date, end_date)

def show_sidebar():
    """Render the sidebar controls"""
    with st.sidebar:
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
            default=config.TOPICS[selected_topic][:3]
        )
        
        # Source filtering
        selected_sources = st.multiselect(
            "Filter by Sources",
            options=config.SOURCES,
            default=['Bloomberg', 'Reuters', 'CNBC']
        )
        
        # Time period
        days_back = st.slider("Analysis Period (Days)", 1, 30, 7)
        
        # Additional filters
        min_sentiment = st.slider(
            "Minimum Sentiment Score",
            -1.0, 1.0, -1.0
        )
        
        return selected_tickers, selected_sources, days_back, min_sentiment

def show_main_content(df, min_sentiment):
    """Render the main dashboard content"""
    
    if df.empty:
        st.warning("No news articles match your filters")
        return
    
    # Filter by sentiment
    df = df[df['vader_compound'] >= min_sentiment]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    avg_sentiment = df['vader_compound'].mean()
    col1.metric("Average Sentiment", f"{avg_sentiment:.2f}", 
               "Positive" if avg_sentiment > 0 else "Negative")
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
        show_raw_data(df)

def show_sentiment_analysis(df):
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
        labels={'vader_compound': 'Sentiment Score'}
    )
    st.plotly_chart(fig2, use_container_width=True)

def show_ticker_comparison(df):
    """Compare sentiment across tickers"""
    st.subheader("Ticker Sentiment Comparison")
    
    # First ensure we have valid data
    if df.empty or 'tickers' not in df.columns or 'vader_compound' not in df.columns:
        st.warning("No valid data available for ticker comparison")
        return
    
    try:
        # Explode the tickers lists into separate rows
        exploded_df = df.explode('tickers')
        
        # Remove any rows with None/NaN tickers
        exploded_df = exploded_df[exploded_df['tickers'].notna()]
        
        # Calculate average sentiment per ticker
        ticker_sentiment = exploded_df.groupby('tickers', observed=True).agg(
            mean_sentiment=('vader_compound', 'mean'),
            article_count=('title', 'count')
        ).sort_values('mean_sentiment')
        
        # Create visualization
        if not ticker_sentiment.empty:
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
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No ticker sentiment data available after processing")
            
    except Exception as e:
        st.error(f"Error generating ticker comparison: {str(e)}")

def show_source_analysis(df):
    """Analyze news sources"""
    st.subheader("Source Analysis")
    
    # Source credibility scoring
    credibility_scores = {
        'Bloomberg': 9.5,
        'Reuters': 9.5,
        'Wall Street Journal': 9.0,
        'Financial Times': 9.0,
        'CNBC': 8.5,
        'MarketWatch': 8.0,
        'Seeking Alpha': 7.5,
        'Investor\'s Business Daily': 8.0,
        'Barron\'s': 8.5
    }
    
    # Add credibility to dataframe
    df['credibility'] = df['source'].map(credibility_scores).fillna(7.0)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Source Distribution", "Source Credibility"])
    
    with tab1:
        source_counts = df['source'].value_counts().nlargest(10)
        fig1 = px.pie(
            source_counts,
            names=source_counts.index,
            values=source_counts.values,
            title="Top News Sources"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        source_stats = df.groupby('source').agg({
            'vader_compound': 'mean',
            'credibility': 'first'
        }).sort_values('credibility', ascending=False)
        
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

def show_raw_data(df):
    """Display raw data with filtering options"""
    st.subheader("Article Data")
    
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
        (df['source'].isin(selected_sources))
    ].sort_values('published', ascending=False)
    
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
        use_container_width=True
    )
@st.cache_data(ttl=config.CACHE_TTL)
def fetch_data_from_csv(csv_path, days_back):
    """Fetch stock data from a CSV file"""
    # Load data from CSV
    df = pd.read_csv(csv_path)
    
    # Convert published column to datetime
    df['published'] = pd.to_datetime(df['published'])
    
    # Filter data by the date range (if needed)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    df_filtered = df[(df['published'] >= start_date) & (df['published'] <= end_date)]
    
    if df_filtered.empty:
        st.warning("No news articles found for the selected time period.")
    else:
        st.write("Fetched articles:", len(df_filtered))
    
    return df_filtered

@st.cache_data(ttl=config.CACHE_TTL)
def fetch_data_from_csv(csv_path):
    # Read CSV
    news_df = pd.read_csv(csv_path)
    
    # Check if the necessary columns exist
    required_columns = ['publishedAt', 'urlToImage', 'source', 'title', 'description', 'url']
    for col in required_columns:
        if col not in news_df.columns:
            st.error(f"Missing column: {col}")
            return None

    # Convert 'publishedAt' column to datetime and ensure it's in UTC
    news_df['publishedAt'] = pd.to_datetime(news_df['publishedAt'], errors='coerce', utc=True)
    
    # Filter by date (example, showing articles from the last 7 days)
    news_df = news_df[news_df['publishedAt'] >= pd.to_datetime('today', utc=True) - pd.Timedelta(days=7)]

    return news_df

def main():
    """Main application function"""
    st.title("📰 Financial News Sentiment Dashboard")
    
    #news = fetch_news_api(config.DEFAULT_TICKERS, config.TIME_WINDOW.days)
     
    csv_path = "data/convertcsv.csv"  # Replace with the actual path to the CSV file
    news_df = pd.read_csv(csv_path)
    df = pd.DataFrame(news_df)

    # Displaying the news swiper
    #st.title("📰 News Swiper")

    # Track the index of the article being displayed
    if 'index' not in st.session_state:
        st.session_state.index = 0

    # Display current article
    
    article = df.iloc[st.session_state.index]
    col1, col2 = st.columns(2)
    with col1:
        st.image(article['urlToImage'], caption=f"Source: {article['source']}", width=200)
        col3, col4 = st.columns([1, 1])
        with col3:
            if st.button("Previous") and st.session_state.index > 0:
                st.session_state.index -= 1
        with col4:
            if st.button("Next") and st.session_state.index < len(df) - 1:
                st.session_state.index += 1
    with col2:
        st.subheader(article['title'])
        st.markdown(article['description'])
        st.markdown(f"[Read more]({article['url']})")

    # Navigation buttons
    
          
 
    
    # Get user inputs from sidebar
    selected_tickers, selected_sources, days_back, min_sentiment = show_sidebar()
    
    if not selected_tickers:
        st.warning("Please select at least one ticker")
        return
    
    # Fetch and process data
    with st.spinner("Fetching and analyzing news..."):
        news_df = fetch_data(selected_tickers, days_back)
        
        if not news_df.empty:
            # Apply source filtering
            news_df = news_df[news_df['source'].isin(selected_sources)]
            
            # Analyze sentiment
            analyzed_df = analyzer.analyze_dataframe(news_df)
            
            # Show main content
            show_main_content(analyzed_df, min_sentiment)
        else:
            st.error("""
            No news articles found. Possible reasons:
            - No recent news for selected tickers
            - API rate limit reached
            - Selected sources didn't cover these tickers
            """)

if __name__ == "__main__":
    main()