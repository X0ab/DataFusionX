# Financial Data Aggregator

## Overview
This project fetches financial data from multiple sources: **Yahoo Finance**, **Financial Times**, and **Twitter/X**. It retrieves stock prices, news articles, and social media sentiment.
# Key Features

## 📰 Multi-API Data Collection
- Integrates seamlessly with **NewsAPI**, **Alpha Vantage**, and **Finnhub**
- Automatically fetches and aggregates financial news and sentiment data
- Includes robust error handling for unreliable or failed API responses

## 💾 Automatic Data Storage
- Stores collected data in a structured **CSV** format
- Updates existing files without creating duplicates
- Ensures data consistency across collection sessions

## 🧠 Complete Sentiment Analysis
- Utilizes **VADER** for natural language sentiment analysis
- Categorizes news as **positive**, **neutral**, or **negative**
- Generates detailed **compound sentiment scores** for precision

## 📊 Interactive Dashboard
- Offers intuitive filtering by **tickers**, **time period**, and **data source**
- Displays sentiment **trends over time** and **distribution visualizations**
- Enables **comparison across tickers and sources** for deeper insights

## ⚙️ Data Normalization
- Transforms diverse API outputs into a **standardized format**
- Smoothly manages missing or incomplete data fields
- Facilitates consistent downstream processing and analysis

## Installation

### Using Poetry
```sh
git clone https://github.com/X0ab/DataFusionX.git
cd DataFusionX
poetry install

```sh 
pip install streamlit newsapi requests vaderSentiment plotly pandas