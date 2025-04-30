from django.http import HttpResponse
from .models import Tweet
import tweepy  # Ensure tweepy is imported and configured
from django.conf import settings

# Setup Tweepy API (make sure you've set keys in your .env and settings)
auth = tweepy.OAuthHandler(
    settings.TWITTER_API_KEY,
    settings.TWITTER_API_SECRET
)
auth.set_access_token(
    settings.TWITTER_ACCESS_TOKEN,
    settings.TWITTER_ACCESS_SECRET
)
api = tweepy.API(auth)




def fetch_and_save_tweets(query="vaccines OR vaccine OR vax OR immunization OR immunize OR vaccination OR polio", count=100):
    geocode = "-1.2921,36.8219,50km"  # Coordinates for Nairobi, Kenya

    tweets = tweepy.Cursor(api.search_tweets, q=query, lang="en", tweet_mode="extended", geocode=geocode).items(count)

    saved = 0
    for tweet in tweets:
        if not Tweet.objects.filter(tweet_id=tweet.id_str).exists():
            Tweet.objects.create(
                tweet_id=tweet.id_str,
                username=tweet.user.screen_name,
                content=tweet.full_text,
                created_at=tweet.created_at,
                tweet_source=tweet.source,
                retweet_count=tweet.retweet_count,
                favorite_count=tweet.favorite_count,
                language=tweet.lang,
                geocoordinates=tweet.coordinates['coordinates'] if tweet.coordinates else None
            )
            saved += 1

    return f"{saved} new tweets saved to the database."


# View for calling it from browser or frontend
def fetch_tweets_view(request):
    result = fetch_and_save_tweets()
    return HttpResponse(result)
