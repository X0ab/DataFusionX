import sqlite3
import pandas as pd
from datetime import datetime
from ..config import settings

class DatabaseStorage:
    def __init__(self):
        self.conn = sqlite3.connect(settings.DATABASE_CONFIG['db_path'])
        self.table_name = settings.DATABASE_CONFIG['table_name']
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database tables if they don't exist"""
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            url TEXT UNIQUE,
            content TEXT,
            source_name TEXT,
            published DATETIME,
            tickers TEXT,  # Stored as comma-separated string
            sentiment_score REAL,
            type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.conn.execute(create_table_query)
        self.conn.commit()
    
    def save_data(self, df):
        """Save DataFrame to database"""
        if df.empty:
            return
        
        # Prepare data for insertion
        df['tickers'] = df['tickers'].apply(lambda x: ",".join(x))
        df['published'] = pd.to_datetime(df['published']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert or ignore duplicates
        insert_query = f"""
        INSERT OR IGNORE INTO {self.table_name}
        (source, title, url, content, source_name, published, tickers, sentiment_score, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        data_to_insert = df[[
            'source', 'title', 'url', 'content', 'source_name', 
            'published', 'tickers', 'sentiment_score', 'type'
        ]].values.tolist()
        
        cursor = self.conn.cursor()
        cursor.executemany(insert_query, data_to_insert)
        self.conn.commit()
    
    def load_data(self, tickers=None, start_date=None, end_date=None, limit=1000):
        """Load data from database with optional filters"""
        query = f"SELECT * FROM {self.table_name}"
        conditions = []
        params = []
        
        if tickers:
            # Create conditions for each ticker
            ticker_conditions = []
            for ticker in tickers:
                ticker_conditions.append("tickers LIKE ?")
                params.append(f"%{ticker}%")
            conditions.append(f"({' OR '.join(ticker_conditions)})")
        
        if start_date:
            conditions.append("published >= ?")
            params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        if end_date:
            conditions.append("published <= ?")
            params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY published DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, self.conn, params=params if params else None)
        
        # Convert tickers back to list
        if not df.empty and 'tickers' in df.columns:
            df['tickers'] = df['tickers'].str.split(',')
        
        # Convert dates
        if not df.empty and 'published' in df.columns:
            df['published'] = pd.to_datetime(df['published'])
        
        return df
    
    def cleanup_old_data(self, days=30):
        """Remove data older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        delete_query = f"DELETE FROM {self.table_name} WHERE published < ?"
        self.conn.execute(delete_query, (cutoff_date,))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()