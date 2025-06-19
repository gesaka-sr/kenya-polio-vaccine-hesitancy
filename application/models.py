from django.db import models

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

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} | {self.url}"


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    author_id = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    text = models.TextField()
    retweet_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)

    # Optional: For differentiating between main tweets and replies
    is_reply = models.BooleanField(default=False)
    conversation_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.tweet_id} by {self.author_id}"

# class TweetURL(models.Model):



