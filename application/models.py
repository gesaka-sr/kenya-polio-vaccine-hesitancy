from django.db import models

# Create your models here.

class Tweet(models.Model):
    tweet_id = models.CharField(max_length=255, unique=True)  # The unique ID of the tweet
    username = models.CharField(max_length=255)  # Twitter username of the user who posted the tweet
    content = models.TextField()  # Full text of the tweet
    created_at = models.DateTimeField()  # Date and time the tweet was created
    tweet_source = models.CharField(max_length=255, null=True, blank=True)  # The platform from where the tweet was posted (e.g., Twitter Web App, Twitter for iPhone)
    retweet_count = models.IntegerField(default=0)  # Number of retweets
    favorite_count = models.IntegerField(default=0)  # Number of likes (favorites)
    language = models
    
    
from .models import Tweet

def fetch_and_save_tweets(query="data science", count=100):
    tweets = tweepy.Cursor(api.search_tweets, q=query, lang="en", tweet_mode="extended").items(count)
    
    for tweet in tweets:
        tweet_id = tweet.id_str
        username = tweet.user.screen_name
        content = tweet.full_text
        created_at = tweet.created_at
        tweet_source = tweet.source
        retweet_count = tweet.retweet_count
        favorite_count = tweet.favorite_count
        language = tweet.lang

        # Save tweet data to database
        Tweet.objects.create(
            tweet_id=tweet_id,
            username=username,
            content=content,
            created_at=created_at,
            tweet_source=tweet_source,
            retweet_count=retweet_count,
            favorite_count=favorite_count,
            language=language
        )

    return f"{count} tweets have been successfully saved to the database."

