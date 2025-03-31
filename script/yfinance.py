import yfinance as yf
import typer



app = typer.Typer(help="Legaldoc Workflow - fetching and parsing tools.")


@app.command()
def main() : 
    # Get stock data for Apple
    apple = yf.Ticker("AAPL") 
    # Get historical market data
    hist = apple.history(period="1mo")
    print(hist)

    # Get current stock price
    current_price = apple.info["regularMarketPrice"]
    print(current_price)
    
    news = apple.news
    for item in news[:5]:  # Afficher les 5 premières actualités
        item = item["content"]
        print(item["title"], "-", item["previewUrl"])

def run():
    app()


if __name__ == "__main__":
    run()