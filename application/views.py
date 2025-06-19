import base64
import httpx
import time
import json
import csv
import os
import asyncio
import requests
from pathlib import Path
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import TweetURLForm
from django.contrib import messages
from collections import defaultdict
from .models import TweetURL, Tweet, CATEGORY_CHOICES
from .sentiment_analysis import process_all_csvs
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 5

logger = logging.getLogger(__name__)

# ---------------------- Utility Functions ----------------------

def submit_tweet_url(request):
    if request.method == 'POST':
        form = TweetURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if not TweetURL.objects.filter(url=url).exists():
                form.save()
                messages.success(request, "✅ URL saved successfully!")
            else:
                messages.warning(request, "⚠️ This URL already exists in the database.")
            return redirect('submit_tweet_url')
    else:
        form = TweetURLForm()

    urls = TweetURL.objects.all()
    return render(request, 'submit_url.html', {'form': form, 'urls': urls})


def generate_bearer_token():
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


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def fetch_with_retry(client, url, params, headers, label=""):
    delay = 60
    for attempt in range(1, MAX_RETRIES + 1):
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"⚠️ Rate limit hit while fetching {label}. Sleeping for {delay} seconds (retry {attempt}/{MAX_RETRIES})")
            await asyncio.sleep(delay)
            delay *= 2
        else:
            response.raise_for_status()
    raise Exception(f"Failed to fetch {label} after {MAX_RETRIES} retries.")


async def fetch_tweets_async(batch_ids, bearer_token):
    async with httpx.AsyncClient() as client:
        url = "https://api.twitter.com/2/tweets"
        params = {
            "ids": ",".join(batch_ids),
            "tweet.fields": "author_id,created_at,public_metrics,conversation_id,text"
        }
        headers = {"Authorization": f"Bearer {bearer_token}"}
        result = await fetch_with_retry(client, url, params, headers, label="tweets")
        return result.get("data", [])


async def fetch_replies_async(conversation_id, bearer_token):
    async with httpx.AsyncClient() as client:
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            "query": f"conversation_id:{conversation_id}",
            "tweet.fields": "author_id,created_at,public_metrics,conversation_id,in_reply_to_user_id,text",
            "max_results": 100
        }
        result = await fetch_with_retry(client, url, params, headers, label="replies")
        return result.get("data", [])


# ---------------------- View ----------------------

def fetch_tweets_view(request):
    bearer_token = generate_bearer_token()
    tweet_objs = TweetURL.objects.all()
    tweet_ids = [url.url.rstrip("/").split("/")[-1] for url in tweet_objs]
    tweet_id_to_obj = {url.url.rstrip("/").split("/")[-1]: url for url in tweet_objs}
    tweet_id_to_category = {tid: obj.category for tid, obj in tweet_id_to_obj.items()}
    CATEGORY_KEYS = [choice[0] for choice in CATEGORY_CHOICES]
    all_tweets_by_category = defaultdict(list)

    cached_ids = set(Tweet.objects.filter(tweet_id__in=tweet_ids).values_list('tweet_id', flat=True))
    ids_to_fetch = [tid for tid in tweet_ids if tid not in cached_ids]

    async def fetch_all():
        for batch in chunks(ids_to_fetch, 100):
            tweets = await fetch_tweets_async(batch, bearer_token)

            for t in tweets:
                tweet_id = t["id"]
                parent_url_obj = tweet_id_to_obj.get(tweet_id)

                data = {
                    "tweet_id": tweet_id,
                    "author_id": t["author_id"],
                    "username": "unknown",
                    "language": "unknown",
                    "text": t["text"],
                    "created_at": t["created_at"],
                    "retweet_count": t["public_metrics"]["retweet_count"],
                    "reply_count": t["public_metrics"]["reply_count"],
                    "like_count": t["public_metrics"]["like_count"],
                    "quote_count": t["public_metrics"]["quote_count"],
                    "favorite_count": None,
                    "is_reply": False,
                    "parent_url": parent_url_obj
                }

                Tweet.objects.update_or_create(tweet_id=tweet_id, defaults=data)

                category = parent_url_obj.category if parent_url_obj else None
                if category in CATEGORY_KEYS:
                    all_tweets_by_category[category].append(data)

                replies = await fetch_replies_async(t["conversation_id"], bearer_token)
                for reply in replies:
                    reply_data = {
                        "tweet_id": reply["id"],
                        "author_id": reply["author_id"],
                        "username": "unknown",
                        "language": "unknown",
                        "text": reply["text"],
                        "created_at": reply["created_at"],
                        "retweet_count": reply["public_metrics"]["retweet_count"],
                        "reply_count": reply["public_metrics"]["reply_count"],
                        "like_count": reply["public_metrics"]["like_count"],
                        "quote_count": reply["public_metrics"]["quote_count"],
                        "favorite_count": None,
                        "is_reply": True,
                        "parent_url": parent_url_obj
                    }
                    Tweet.objects.update_or_create(tweet_id=reply_data["tweet_id"], defaults=reply_data)

                    if category in CATEGORY_KEYS:
                        all_tweets_by_category[category].append(reply_data)

    asyncio.run(fetch_all())

    # Include cached tweets
    for ct in Tweet.objects.filter(tweet_id__in=cached_ids):
        category = tweet_id_to_category.get(ct.tweet_id)
        if category in CATEGORY_KEYS:
            all_tweets_by_category[category].append({
                "tweet_id": ct.tweet_id,
                "author_id": ct.author_id,
                "created_at": ct.created_at.isoformat(),
                "text": ct.text,
                "retweet_count": ct.retweet_count,
                "reply_count": ct.reply_count,
                "like_count": ct.like_count,
                "quote_count": ct.quote_count,
                "parent_tweet": ct.parent_tweet,
                "is_reply": ct.is_reply
            })

    # Output files
    output_dir = Path(settings.MEDIA_ROOT)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_links = {}
    for category in CATEGORY_KEYS:
        tweets = all_tweets_by_category.get(category, [])
        if not tweets:
            continue
        json_filename = f"{category}_tweets.json"
        csv_filename = f"{category}_tweets.csv"
        json_path = output_dir / json_filename
        csv_path = output_dir / csv_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)

        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=tweets[0].keys())
            writer.writeheader()
            writer.writerows(tweets)

        file_links[category] = {
            "json_url": os.path.join(settings.MEDIA_URL, json_filename),
            "csv_url": os.path.join(settings.MEDIA_URL, csv_filename),
            "count": len(tweets)
        }

    return render(request, "download_links.html", {
        "file_links": file_links,
        "category_keys": CATEGORY_KEYS
    })