import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from news_fetchers.alpha_vantage import AlphaVantageFetcher
from analyzers.sentiment_analyzer import SentimentAnalyzer
from config.settings import Config

# Set up page config
st.set_page_config(
    page_title="Financial News Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize components
config = Config()
analyzer = SentimentAnalyzer()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_data(tickers, days_back):
    fetcher = AlphaVantageFetcher(config.API_KEYS['alpha_vantage'])
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return fetcher.fetch_news(tickers, start_date, end_date)

def main():
    st.title("📰 Financial News Sentiment Analyzer")
    
    with st.sidebar:
        st.header("Settings")
        selected_tickers = st.multiselect(
            "Select Tickers",
            options=config.DEFAULT_TICKERS,
            default=["AAPL", "MSFT"]
        )
        days_back = st.slider("Analysis Period (Days)", 1, 30, 7)
        analyze_button = st.button("Analyze News")
    
    if analyze_button and selected_tickers:
        with st.spinner("Fetching and analyzing news..."):
            news_df = fetch_data(selected_tickers, days_back)
            
            if news_df.empty:
                st.error("No news articles found. Try different tickers or a shorter time period.")
                return
                
            analyzed_df = analyzer.analyze_dataframe(news_df)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            avg_sentiment = analyzed_df['vader_compound'].mean()
            col1.metric("Average Sentiment", f"{avg_sentiment:.2f}", 
                       "Positive" if avg_sentiment > 0 else "Negative")
            col2.metric("Total Articles", len(analyzed_df))
            col3.metric("Sources", analyzed_df['source'].nunique())
            
            # Visualizations
            st.header("News Sentiment Analysis")
            tab1, tab2, tab3, tab4 = st.tabs(["Sentiment Trend", "Ticker Comparison", "Source Analysis", "Raw Data"])
            
            with tab1:
                plot_sentiment_trend(analyzed_df)
                
            with tab2:
                plot_ticker_comparison(analyzed_df)
                
            with tab3:
                plot_source_analysis(analyzed_df)
                
            with tab4:
                st.dataframe(analyzed_df.sort_values('published', ascending=False))

def plot_sentiment_trend(df):
    df['date'] = pd.to_datetime(df['published']).dt.date
    daily_sentiment = df.groupby(['date', 'sentiment_label']).size().unstack().fillna(0)
    
    fig = px.area(
        daily_sentiment,
        title="Daily Sentiment Trend",
        labels={'value': 'Number of Articles', 'date': 'Date'},
        color_discrete_map={
            'positive': '#2ecc71',
            'neutral': '#f1c40f',
            'negative': '#e74c3c'
        }
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

def plot_ticker_comparison(df):
    # First explode the tickers lists into separate rows
    exploded_df = df.explode('tickers')
    
    # Now group by individual tickers
    ticker_sentiment = exploded_df.groupby('tickers')['vader_compound'].mean().sort_values()
    
    # Create the visualization
    fig = px.bar(
        ticker_sentiment,
        orientation='h',
        title="Average Sentiment by Ticker",
        color=ticker_sentiment,
        color_continuous_scale='RdYlGn',
        labels={'value': 'Sentiment Score', 'index': 'Ticker'}
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

def plot_source_analysis(df):
    col1, col2 = st.columns(2)
    
    with col1:
        source_counts = df['source'].value_counts().nlargest(10)
        fig1 = px.pie(
            source_counts,
            names=source_counts.index,
            values=source_counts.values,
            title="Top News Sources"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        source_sentiment = df.groupby('source')['vader_compound'].mean().nlargest(10)
        fig2 = px.bar(
            source_sentiment,
            title="Average Sentiment by Source",
            labels={'value': 'Sentiment Score', 'index': 'Source'}
        )
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()