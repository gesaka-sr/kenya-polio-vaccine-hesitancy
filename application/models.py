from django.db import models

class Tweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    author_id = models.CharField(max_length=50)
    username = models.CharField(max_length=100, blank=True, null=True)  # Optional Twitter handle
    language = models.CharField(max_length=10, blank=True, null=True)   # Tweet language
    created_at = models.DateTimeField()
    text = models.TextField()
    retweet_count = models.IntegerField()
    reply_count = models.IntegerField()
    like_count = models.IntegerField()
    quote_count = models.IntegerField()
    favorite_count = models.IntegerField(blank=True, null=True)  # Legacy metric (optional)

    def __str__(self):
        return f"Tweet {self.tweet_id}"

class TweetURL(models.Model):
    CATEGORY_CHOICES = [
        ('education', 'Education'),
        ('health', 'Health'),
        ('transport', 'Transport'),
        ('security', 'Security'),
        ('trade_economics', 'Trade and Economics'),
        ('politics', 'Politics'),
        ('other', 'Other'),
    ]

    url = models.URLField(unique=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Select a category for this Tweet URL"
    )

    def __str__(self):
        return f"{self.url} ({self.get_category_display()})"
