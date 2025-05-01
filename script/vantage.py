import typer
from dotenv import load_dotenv
import requests
import os

app = typer.Typer(help="Legaldoc Workflow - fetching and parsing tools.")


@app.command()
def main() : 
    
    load_dotenv('.env.local') 
    # Get your Bearer Token from environment variables
    api_key = os.getenv('VANTAGE_ACCESS_TOKEN')
    symbol = 'IBM'  # Apple stock symbol 
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    print(data)

def run():
    app()


if __name__ == "__main__":
    run()