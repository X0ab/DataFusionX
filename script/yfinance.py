import yfinance as yf

# Get stock data for Apple
apple = yf.Ticker("AAPL")

# Get historical market data
hist = apple.history(period="1mo")
print(hist)

# Get current stock price
current_price = apple.info["regularMarketPrice"]
print(current_price)
