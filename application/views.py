from django.http import HttpResponse


from .utils import fetch_and_save_tweets  # Import the function
import tweepy
from datetime import datetime
from django.shortcuts import render
from .models import Tweet

# Twitter API credentials (replace with your own)
consumer_key = 'your_consumer_key'
consumer_secret = 'your_consumer_secret'
access_token = 'your_access_token'
access_token_secret = 'your_access_token_secret'

# Set up Tweepy authentication
auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, access_token, access_token_secret
)
api = tweepy.API(auth)

def home(request):
    return HttpResponse("Hello from myapp!")
# Function to fetch and save tweets
def fetch_and_save_tweets(query="data science", count=100):
    # Fetch tweets using Tweepy
    tweets = tweepy.Cursor(api.search_tweets, q=query, lang="en", tweet_mode="extended").items(count)
    
    for tweet in tweets:
        tweet_id = tweet.id_str
        username = tweet.user.screen_name
        content = tweet.full_text
        created_at = tweet.created_at
        
        # Save tweet to database
        Tweet.objects.create(
            tweet_id=tweet_id,
            username=username,
            content=content,
            created_at=created_at
        )

    return f"{count} tweets have been successfully saved to the database."



def fetch_tweets(request):
    result = fetch_and_save_tweets(query="data science", count=100)
    return HttpResponse(result)
