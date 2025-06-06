import base64
import requests
import tweepy
import time
import csv
import json
from django.http import HttpResponse
from django.conf import settings
from .models import Tweet

# List of all tweet URLs you want data for
tweet_urls = [
    "https://x.com/GrandPRKE/status/1855463721838969104",
    "https://x.com/MOH_Kenya/status/1841772181358780732",
    "https://x.com/ntvkenya/status/1841886549035675707",
    "https://x.com/ntvkenya/status/1841892124440092753",
    "https://x.com/MOH_Kenya/status/1842070347949945240",
    "https://x.com/MOH_Kenya/status/1842443214688547177",
    "https://x.com/MOH_Kenya/status/1842456497390776361",
    "https://x.com/MOH_Kenya/status/1844399101762298049",
    "https://x.com/MOH_Kenya/status/1847313709518999739",
    "https://x.com/MOH_Kenya/status/1854976082556096979",
    "https://x.com/MOH_Kenya/status/1855188210831212824",
    "https://x.com/MOH_Kenya/status/1855290251310403594",
    "https://x.com/MOH_Kenya/status/1855297207626264635",
    "https://x.com/MOH_Kenya/status/1855309785828082134",
    "https://x.com/MOH_Kenya/status/1855320477654528254",
    "https://x.com/MOH_Kenya/status/1855327135587573863",
    "https://x.com/Lasterbosire/status/1855327708492038499",
    "https://x.com/MOH_Kenya/status/1855337856824475693",
    "https://x.com/MOH_Kenya/status/1855343194466394284",
    "https://x.com/MOH_Kenya/status/1855552463480193368",
    "https://x.com/MOH_Kenya/status/1855560071960244689",
    "https://x.com/MOH_Kenya/status/1855569000031191106",
    "https://x.com/TurkanaCountyKE/status/1855572816877285376",
    "https://x.com/MOH_Kenya/status/1855627239011885099",
    "https://x.com/WHOAFRO/status/1855624457177477150",
    "https://x.com/MOH_Kenya/status/1855939598775382041",
    "https://x.com/MOH_Kenya/status/1855972319304286252",
    "https://x.com/UNICEFKenya/status/1855960738604442019",
    "https://x.com/MOH_Kenya/status/1856266615425310924",
    "https://x.com/MOH_Kenya/status/1856653253712257234",
    "https://x.com/MOH_Kenya/status/1856902944207106461",
    "https://x.com/MOH_Kenya/status/1856897251806716192",
    "https://x.com/MOH_Kenya/status/1856281568874246455",
]

def extract_tweet_ids_with_urls(urls):
    """
    Extract tweet IDs from URLs and map ID to URL.
    """
    id_url_map = {}
    for url in urls:
        tweet_id = url.rstrip('/').split('/')[-1]
        if tweet_id.isdigit():
            id_url_map[tweet_id] = url
    return id_url_map

def generate_bearer_token():
    """
    Generate bearer token using Twitter API keys from settings.
    """
    key_secret = f"{settings.TWITTER_API_KEY}:{settings.TWITTER_API_SECRET}".encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret).decode('ascii')

    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers={
            "Authorization": f"Basic {b64_encoded_key}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        data={"grant_type": "client_credentials"}
    )
    if response.status_code != 200:
        raise Exception(f"Bearer token request failed: {response.text}")
    return response.json()["access_token"]

def fetch_and_save_tweets_by_ids(tweet_id_url_map):
    try:
        print("Fetching bearer token...")
        bearer_token = generate_bearer_token()

        print("Creating Tweepy client...")
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

        all_tweet_data = []
        tweet_ids = list(tweet_id_url_map.keys())
        missing_tweets = []

        # Twitter API allows up to 100 IDs per request
        for i in range(0, len(tweet_ids), 100):
            batch_ids = tweet_ids[i:i+100]
            try:
                print(f"Fetching tweets for batch: {batch_ids}")
                response = client.get_tweets(
                    ids=batch_ids,
                    tweet_fields=["created_at", "lang", "source", "public_metrics", "geo"],
                    expansions=["author_id"],
                    user_fields=["username"]
                )

                fetched_tweets = response.data or []
                users = {user.id: user for user in response.includes.get("users", [])} if response.includes else {}

                # Track which tweets were fetched in this batch
                fetched_ids = {str(tweet.id) for tweet in fetched_tweets}
                missing_in_batch = set(batch_ids) - fetched_ids
                missing_tweets.extend(missing_in_batch)

                for tweet in fetched_tweets:
                    author = users.get(tweet.author_id)
                    username = author.username if author else "unknown"

                    tweet_record = {
                        "tweet_id": str(tweet.id),
                        "tweet_url": tweet_id_url_map.get(str(tweet.id), "unknown"),
                        "username": username,
                        "content": tweet.text,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "tweet_source": getattr(tweet, "source", "unknown"),
                        "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                        "favorite_count": tweet.public_metrics.get("like_count", 0),
                        "language": tweet.lang or "und",
                        "geocoordinates": tweet.geo if hasattr(tweet, 'geo') else None,
                    }

                    # Save to DB if not exists
                    if not Tweet.objects.filter(tweet_id=tweet_record["tweet_id"]).exists():
                        Tweet.objects.create(**tweet_record)
                        print(f"Saved tweet {tweet.id}")
                    else:
                        print(f"Tweet {tweet.id} already exists")

                    all_tweet_data.append(tweet_record)

                time.sleep(2)  # small delay to respect rate limits

            except tweepy.TooManyRequests:
                print("Rate limit hit, sleeping 60 seconds...")
                time.sleep(60)
                continue
            except Exception as e:
                print(f"Error fetching batch {batch_ids}: {e}")
                continue

        # Save all fetched data to JSON and CSV files
        if all_tweet_data:
            json_file_path = "tweets_output.json"
            csv_file_path = "tweets_output.csv"

            with open(json_file_path, "w", encoding="utf-8") as f_json:
                json.dump(all_tweet_data, f_json, ensure_ascii=False, indent=4)

            with open(csv_file_path, "w", encoding="utf-8", newline='') as f_csv:
                writer = csv.DictWriter(f_csv, fieldnames=all_tweet_data[0].keys())
                writer.writeheader()
                writer.writerows(all_tweet_data)

            print(f"Saved all tweets to '{json_file_path}' and '{csv_file_path}'.")

        if missing_tweets:
            print(f"Could not fetch {len(missing_tweets)} tweets. Missing IDs:")
            for mid in missing_tweets:
                print(f"{mid} -> {tweet_id_url_map.get(mid)}")

        return f"Fetched and saved {len(all_tweet_data)} tweets; {len(missing_tweets)} tweets missing."

    except Exception as e:
        print(f"Fatal error in fetching tweets: {e}")
        raise

def fetch_tweets_view(request):
    try:
        tweet_id_url_map = extract_tweet_ids_with_urls(tweet_urls)
        result = fetch_and_save_tweets_by_ids(tweet_id_url_map)
        return HttpResponse(result)
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)
