from django.http import HttpResponse
from .models import Tweet
import snscrape.modules.twitter as sntwitter


def fetch_and_save_view(count=100):
    query = '(vaccines OR vaccine OR vax OR immunization OR immunize OR vaccination OR polio) lang:en geocode:-1.2921,36.8219,100km'
    tweet_count = 0
    saved_tweet_ids = []

    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if tweet_count >= count:
            break

        obj, created = Tweet.objects.get_or_create(
            tweet_id=str(tweet.id),
            defaults={
                'username': tweet.user.username,
                'content': tweet.content,
                'created_at': tweet.date,
                'retweet_count': tweet.retweetCount,
                'favorite_count': tweet.likeCount,
                'language': tweet.lang,
                'geocoordinates': f"{tweet.coordinates}" if tweet.coordinates else None
            }
        )

        if created:
            saved_tweet_ids.append(str(tweet.id))
            tweet_count += 1

    if saved_tweet_ids:
        return f"{tweet_count} tweets saved. Tweet IDs:\n" + "\n".join(saved_tweet_ids)
    else:
        return "No new tweets were saved."


def fetch_tweets(request):
    result = fetch_and_save_view()
    return HttpResponse(result, content_type="text/plain")
