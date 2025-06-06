from django.contrib import admin
from .models import Tweet

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = (
        "tweet_id",
        "username",
        "author_id",
        "language",
        "created_at",
        "favorite_count",
        "retweet_count",
        "reply_count",
        "like_count",
        "quote_count",
    )
    search_fields = ("tweet_id", "author_id", "username", "text")
