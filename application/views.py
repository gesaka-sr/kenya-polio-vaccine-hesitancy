import base64
import requests
import tweepy
from django.http import HttpResponse
from django.conf import settings
from .models import Tweet


def generate_bearer_token():
    key_secret = f"{settings.TWITTER_API_KEY}:{settings.TWITTER_API_SECRET}".encode('ascii')
    
    b64_encoded_key = base64.b64encode(key_secret).decode('ascii')
    print(b64_encoded_key)
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers={
            "Authorization": f"Basic {b64_encoded_key}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        data={"grant_type": "client_credentials"}
    )

    if response.status_code != 200:
        raise Exception(f"Bearer token request failed: {response.text}")

    return response.json()["access_token"]


def fetch_and_save_tweets(query="(polio OR vaccine OR vaccination) lang:en", max_results=20):
    bearer_token = generate_bearer_token()

    client = tweepy.Client(bearer_token=bearer_token)

    response = client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=["created_at", "lang", "source", "public_metrics", "geo"],
        expansions=["author_id"]
    )

    saved = 0
    tweets = response.data if response.data else []
    users = {u["id"]: u for u in response.includes.get("users", [])} if response.includes else {}

    for tweet in tweets:
        username = users.get(tweet.author_id, {}).get("username", "unknown")
        if not Tweet.objects.filter(tweet_id=tweet.id).exists():
            Tweet.objects.create(
                tweet_id=tweet.id,
                username=username,
                content=tweet.text,
                created_at=tweet.created_at,
                tweet_source=tweet.source,
                retweet_count=tweet.public_metrics["retweet_count"],
                favorite_count=tweet.public_metrics["like_count"],
                language=tweet.lang,
                geocoordinates=None  # Only available in elevated access
            )
            saved += 1

    return f"{saved} new tweets saved to the database."


def fetch_tweets_view(request):
    try:
        result = fetch_and_save_tweets()
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    return HttpResponse(result)
