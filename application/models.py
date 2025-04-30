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
    language = models.CharField(max_length=10, null=True, blank=True)  # Language of the tweet
    geocoordinates = models.JSONField(null=True, blank=True)  # To store coordinates if available


    def __str__(self):
        return f"{self.username}: {self.content[:50]}"  # Display first 50 characters of the tweet in the admin
