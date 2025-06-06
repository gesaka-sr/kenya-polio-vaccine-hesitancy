import base64
import requests
import time
import json
import csv
from pathlib import Path
from django.http import HttpResponse
from django.conf import settings
from .models import Tweet
from django.shortcuts import render, redirect
from .forms import TweetURLForm
from .models import TweetURL
from django.contrib import messages
from application.models import TweetURL
import json, csv, time
import os
from django.utils.dateparse import parse_datetime


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


# ✅ Generate Bearer Token
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

# ✅ Helper to split into chunks
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ✅ Fetch tweets from Twitter API
def fetch_tweets(batch_ids, bearer_token):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    params = {
        "ids": ",".join(batch_ids),
        "tweet.fields": "author_id,created_at,public_metrics"
    }

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            print("⏳ Rate limit hit. Sleeping for 60 seconds...")
            time.sleep(60)
            continue
        response.raise_for_status()
        break

    return response.json().get("data", [])


def fetch_tweets_view(request):
    bearer_token = generate_bearer_token()
    all_tweets = []

    # Get all tweet URLs from DB
    tweet_urls = TweetURL.objects.values_list('url', flat=True)
    tweet_ids = [url.rstrip("/").split("/")[-1] for url in tweet_urls]

    # Find tweet_ids that are NOT in DB (cache check)
    cached_ids = set(Tweet.objects.filter(tweet_id__in=tweet_ids).values_list('tweet_id', flat=True))
    ids_to_fetch = [tid for tid in tweet_ids if tid not in cached_ids]

    print(f"Fetching {len(ids_to_fetch)} new tweets out of {len(tweet_ids)} total.")

    # Fetch new tweets in batches
    for batch in chunks(ids_to_fetch, 100):
        tweets = fetch_tweets(batch, bearer_token)
        for t in tweets:
            data = {
                "tweet_id": t["id"],
                "author_id": t["author_id"],
                "created_at": t["created_at"],
                "text": t["text"],
                "retweet_count": t["public_metrics"]["retweet_count"],
                "reply_count": t["public_metrics"]["reply_count"],
                "like_count": t["public_metrics"]["like_count"],
                "quote_count": t["public_metrics"]["quote_count"],
            }

            Tweet.objects.update_or_create(
                tweet_id=data["tweet_id"],
                defaults=data
            )

            all_tweets.append(data)
            print(f"✅ Saved Tweet {t['id']}")

        time.sleep(3)  # Respect rate limits

    # Add cached tweets from DB to all_tweets to have a full set (optional)
    cached_tweets = Tweet.objects.filter(tweet_id__in=cached_ids)
    for ct in cached_tweets:
        all_tweets.append({
            "tweet_id": ct.tweet_id,
            "author_id": ct.author_id,
            "created_at": ct.created_at.isoformat(),
            "text": ct.text,
            "retweet_count": ct.retweet_count,
            "reply_count": ct.reply_count,
            "like_count": ct.like_count,
            "quote_count": ct.quote_count,
        })
        time.sleep(3)
    # ✅ Save files to MEDIA folder
    output_dir = Path(settings.MEDIA_ROOT)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_filename = "tweets_output.json"
    csv_filename = "tweets_output.csv"
    json_path = output_dir / json_filename
    csv_path = output_dir / csv_filename

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_tweets, f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_tweets[0].keys())
        writer.writeheader()
        writer.writerows(all_tweets)

    # ✅ Build public file URLs for the template
    json_url = os.path.join(settings.MEDIA_URL, json_filename)
    csv_url = os.path.join(settings.MEDIA_URL, csv_filename)

    return render(request, "download_links.html", {
        "json_url": json_url,
        "csv_url": csv_url,
        "count": len(all_tweets)
    })
