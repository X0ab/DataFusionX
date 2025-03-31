import typer
import tweepy
from dotenv import load_dotenv
import os



app = typer.Typer(help="Legaldoc Workflow - fetching and parsing tools.")


@app.command()
def main() : 


    load_dotenv('.env.local')

    # Get your Bearer Token from environment variables
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    auth = tweepy.OAuth2BearerHandler(bearer_token)
    #auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth) 
    client = tweepy.Client(bearer_token=bearer_token)

    # Perform a recent tweet search (v2 endpoint)
    query = 'Tesla stock'
    response = client.search_recent_tweets(query=query, max_results=10)
    #tweets = api.search_tweets(q="Tesla stock", lang="en", count=10)
     
    # Print the tweet texts
    for tweet in response.data:
        print(tweet.text)
    #for tweet in tweets:
        #print(tweet.user.name, "-", tweet.text)


def run():
    app()


if __name__ == "__main__":
    run()