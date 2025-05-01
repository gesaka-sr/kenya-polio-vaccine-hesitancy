from django.urls import path
from . import views

urlpatterns = [
    path('', views.fetch_tweets_view, name='fetch_tweets_view'),
    # path("api/tweets/", views.fetch_tweets, name="fetch_tweets")# Example view
]