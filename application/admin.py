from django.contrib import admin
from .models import Tweet

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('tweet_id', 'username', 'created_at', 'language', 'retweet_count', 'favorite_count')
    search_fields = ('username', 'content')
    ordering = ('-created_at',)
