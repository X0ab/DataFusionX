import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config.settings import Config

class Dashboard:
    def __init__(self, data):
        self.data = data
        self.config = Config()
        
    def create_dashboard(self):
        fig = make_subplots(
            rows=3, cols=2,
            specs=[
                [{'type': 'indicator'}, {'type': 'pie'}],
                [{'type': 'bar', 'colspan': 2}, None],
                [{'type': 'scatter', 'colspan': 2}, None]
            ],
            subplot_titles=(
                'Market Sentiment', 'News Sources',
                'Top Positive Stocks', 'Sentiment Timeline'
            )
        )
        
        # Add sentiment gauge
        fig.add_trace(self._create_sentiment_gauge(), row=1, col=1)
        
        # Add sources pie chart
        fig.add_trace(self._create_sources_piechart(), row=1, col=2)
        
        # Add top stocks bar chart
        fig.add_trace(self._create_top_stocks_chart(), row=2, col=1)
        
        # Add timeline
        fig.add_trace(self._create_timeline(), row=3, col=1)
        
        fig.update_layout(
            height=1200,
            template='plotly_dark',
            margin=dict(t=100, b=50),
            showlegend=False
        )
        return fig
    
    def _create_sentiment_gauge(self):
        avg_sentiment = self.data['vader_compound'].mean()
        return go.Indicator(
            mode="gauge+number",
            value=avg_sentiment,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [-1, 1]},
                'steps': [
                    {'range': [-1, -0.5], 'color': self.config.COLORS['negative']},
                    {'range': [-0.5, 0], 'color': self.config.COLORS['neutral']},
                    {'range': [0, 0.5], 'color': self.config.COLORS['positive']},
                    {'range': [0.5, 1], 'color': '#27ae60'}
                ]
            }
        )
    
    def _create_sources_piechart(self):
        source_counts = self.data['source'].value_counts()
        return go.Pie(
            labels=source_counts.index,
            values=source_counts.values,
            hole=0.4,
            marker_colors=px.colors.qualitative.Dark24
        )
    
    def _create_top_stocks_chart(self):
        top_tickers = self.data.groupby('tickers')['vader_compound'] \
            .mean().nlargest(10).reset_index()
        return go.Bar(
            x=top_tickers['vader_compound'],
            y=top_tickers['tickers'],
            orientation='h',
            marker_color=self.config.COLORS['positive']
        )
    
    def _create_timeline(self):
        timeline_data = self.data.set_index('published')['vader_compound'] \
            .resample('6H').mean().ffill()
        return go.Scatter(
            x=timeline_data.index,
            y=timeline_data.values,
            mode='lines+markers',
            line_color=self.config.COLORS['neutral']
        )