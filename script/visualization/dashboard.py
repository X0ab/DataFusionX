import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def create_dashboard(processed_news, aggregated_sentiment):
    """Create an interactive Dash dashboard"""
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
    
    # Pre-process data for visualizations
    time_series_df = create_time_series_data(processed_news)
    top_tickers = aggregated_sentiment.nlargest(10, 'vader_compound')
    
    app.layout = dbc.Container([
        dbc.Row(dbc.Col(html.H1("Financial News Sentiment Dashboard", className="text-center my-4"))),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=create_sentiment_gauge(aggregated_sentiment)),
                dcc.Graph(figure=create_sentiment_distribution(processed_news))
            ], md=4),
            
            dbc.Col([
                dcc.Graph(figure=create_sentiment_timeseries(time_series_df)),
                dcc.Graph(figure=create_sentiment_bubble(processed_news))
            ], md=8)
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(figure=create_ticker_barchart(top_tickers)), md=6),
            dbc.Col(dcc.Graph(figure=create_source_piechart(processed_news)), md=6)
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(figure=create_heatmap(processed_news)), width=12)
        ]),
        
        html.Div(id='hover-data', style={'display': 'none'})
    ], fluid=True)
    
    return app

def create_sentiment_timeseries(df):
    """Create interactive time series chart"""
    fig = px.line(df, x='date', y='vader_compound', 
                 color='ticker', title='Sentiment Over Time',
                 template='plotly_dark',
                 hover_data=['title', 'source'])
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Sentiment Score',
        hovermode='x unified',
        height=400
    )
    return fig

def create_ticker_barchart(df):
    """Create horizontal bar chart for top tickers"""
    fig = px.bar(df, x='vader_compound', y='ticker', 
                orientation='h', title='Top Positive Sentiment Stocks',
                color='vader_compound',
                color_continuous_scale='RdYlGn',
                template='plotly_dark')
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=400,
        coloraxis_showscale=False
    )
    return fig

def create_sentiment_gauge(df):
    """Create gauge meter for overall sentiment"""
    avg_sentiment = df['vader_compound'].mean()
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_sentiment,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Market Sentiment"},
        gauge={
            'axis': {'range': [-1, 1]},
            'steps': [
                {'range': [-1, -0.5], 'color': "red"},
                {'range': [-0.5, 0], 'color': "orange"},
                {'range': [0, 0.5], 'color': "lightgreen"},
                {'range': [0.5, 1], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': avg_sentiment
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(t=50, b=10))
    return fig

def create_sentiment_bubble(df):
    """Create bubble chart of sentiment vs subjectivity"""
    fig = px.scatter(df, x='vader_compound', y='textblob_subjectivity',
                    size='vader_positive', color='ticker',
                    hover_name='title', title='Sentiment vs Subjectivity',
                    template='plotly_dark')
    
    fig.update_layout(
        xaxis_range=[-1,1],
        yaxis_range=[0,1],
        height=400
    )
    return fig

def create_source_piechart(df):
    """Create pie chart of news sources"""
    source_counts = df['source'].value_counts().reset_index()
    source_counts.columns = ['source', 'count']
    
    fig = px.pie(source_counts, values='count', names='source',
                title='News Source Distribution',
                hole=0.4, template='plotly_dark')
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    return fig

def create_heatmap(df):
    """Create heatmap of sentiment by ticker and time"""
    pivot_df = df.pivot_table(index='date', columns='ticker', 
                            values='vader_compound', aggfunc='mean')
    
    fig = px.imshow(pivot_df.T,
                   color_continuous_scale='RdYlGn',
                   title='Sentiment Heatmap by Ticker and Date',
                   template='plotly_dark')
    
    fig.update_layout(height=400)
    return fig

def create_time_series_data(df):
    """Prepare time series data"""
    df['date'] = pd.to_datetime(df['published']).dt.date
    return df.groupby(['date', 'ticker']).agg({
        'vader_compound': 'mean',
        'title': 'count',
        'source': 'first'
    }).reset_index()