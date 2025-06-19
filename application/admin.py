from django.contrib import admin
from .models import Tweet, TweetURL

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = (
        "tweet_id",
        "author_id",
        "created_at",
        "is_reply",
        "retweet_count",
        "reply_count",
        "like_count",
        "quote_count",
    )
    search_fields = ("tweet_id", "author_id", "text")
    list_filter = ("is_reply",)
    ordering = ("-created_at",)


@admin.register(TweetURL)
class TweetURLAdmin(admin.ModelAdmin):
    list_display = ("url", "category", "created_at")
    search_fields = ("url", "category")
    ordering = ("-created_at",)
