from django.db import models

class Tweet(models.Model):
    tweet_id = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    created_at = models.DateTimeField()
    retweet_count = models.IntegerField(default=0)
    favorite_count = models.IntegerField(default=0)
    language = models.CharField(max_length=10)
    username = models.CharField(max_length=255)
    # geocoordinates can be optional
    geocoordinates = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.content[:52]
