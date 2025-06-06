from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('tweets', views.fetch_tweets_view, name='fetch_tweets_view'),
    path('', views.submit_tweet_url, name='submit_tweet_url'),
    # path("api/tweets/", views.fetch_tweets, name="fetch_tweets")# Example view
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)