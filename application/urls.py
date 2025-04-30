from django.urls import path
from . import views

urlpatterns = [
    path('', views.fetch_tweets_view, name='fetch_tweets_view'),  # Example view
]