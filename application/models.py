from django.db import models

CATEGORY_CHOICES = [
    ('health', 'Health'),
    ('education', 'Education'),
    ('security', 'Security'),
    ('sports', 'Sports'),
    ('politics', 'Politics'),
    ('technology', 'Technology'),
]

class TweetURL(models.Model):
    url = models.URLField(unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.category.capitalize()} - {self.url}"


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=100, unique=True)
    author_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    text = models.TextField()
    language = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    retweet_count = models.IntegerField()
    reply_count = models.IntegerField()
    like_count = models.IntegerField()
    quote_count = models.IntegerField()
    favorite_count = models.IntegerField(null=True, blank=True)
    is_reply = models.BooleanField(default=False)

    # Parent relationship to TweetURL
    parent_url = models.ForeignKey(TweetURL, on_delete=models.CASCADE, related_name='tweets')

    def __str__(self):
        return self.text[:50]
