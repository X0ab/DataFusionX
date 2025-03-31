import requests
from bs4 import BeautifulSoup
import typer


app = typer.Typer(help="Legaldoc Workflow - fetching and parsing tools.")

@app.command()
def main() : 
    url = "https://www.ft.com/markets"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extraire les titres des articles
    articles = soup.find_all("a", class_="js-teaser-heading-link")  # Vérifier la classe HTML réelle

    for article in articles[:5]:  # Afficher les 5 premiers
        print(article.text.strip(), "-", "https://www.ft.com" + article["href"])

def run():
    app()


if __name__ == "__main__":
    run()