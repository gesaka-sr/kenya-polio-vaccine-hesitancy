import base64
import requests
import time
import csv
import json
import os
from pathlib import Path
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Tweet, TweetURL
from .forms import TweetURLForm


# Extract tweet ID from URL
def extract_tweet_ids_with_urls(urls):
    id_url_map = {}
    for url in urls:
        tweet_id = url.rstrip('/').split('/')[-1]
        if tweet_id.isdigit():
            id_url_map[tweet_id] = url
    return id_url_map


# Submit Tweet URL form
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


# Generate bearer token
def generate_bearer_token():
    key_secret = f"{settings.TWITTER_API_KEY}:{settings.TWITTER_API_SECRET}".encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret).decode('ascii')

    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers={
            "Authorization": f"Basic {b64_encoded_key}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        },
        data={"grant_type": "client_credentials"}
    )

    if response.status_code != 200:
        raise Exception(f"Bearer token request failed: {response.text}")

    return response.json()["access_token"]


# Utility for batching tweet IDs
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# Fetch tweet data from IDs
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


# Fetch replies to a tweet using conversation_id
def fetch_replies(conversation_id, bearer_token):
    replies = []
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    params = {
        "query": f"conversation_id:{conversation_id} is:reply",
        "tweet.fields": "author_id,created_at,public_metrics,conversation_id",
        "max_results": 100
    }

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            print("Rate limit reached while fetching replies. Sleeping for 60 seconds.")
            time.sleep(60)
            continue
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            replies.extend(data["data"])
        if "meta" in data and "next_token" in data["meta"]:
            params["next_token"] = data["meta"]["next_token"]
        else:
            break
    return replies


# Main view to fetch tweets + replies and export
def fetch_tweets_view(request):
    try:
        bearer_token = generate_bearer_token()
        all_tweets = []

        tweet_urls = TweetURL.objects.values_list('url', flat=True)
        tweet_ids = [url.rstrip("/").split("/")[-1] for url in tweet_urls if url.rstrip("/").split("/")[-1].isdigit()]

        cached_ids = set(Tweet.objects.filter(tweet_id__in=tweet_ids).values_list('tweet_id', flat=True))
        ids_to_fetch = [tid for tid in tweet_ids if tid not in cached_ids]

        print(f"Fetching {len(ids_to_fetch)} new tweets out of {len(tweet_ids)} total.")

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
                    "is_reply": False
                }

                Tweet.objects.update_or_create(
                    tweet_id=data["tweet_id"],
                    defaults=data
                )
                all_tweets.append(data)
                print(f"✅ Saved Tweet {t['id']}")

                # Fetch and save replies
                replies = fetch_replies(t["id"], bearer_token)
                for reply in replies:
                    reply_data = {
                        "tweet_id": reply["id"],
                        "author_id": reply["author_id"],
                        "created_at": reply["created_at"],
                        "text": reply["text"],
                        "retweet_count": reply["public_metrics"]["retweet_count"],
                        "reply_count": reply["public_metrics"]["reply_count"],
                        "like_count": reply["public_metrics"]["like_count"],
                        "quote_count": reply["public_metrics"]["quote_count"],
                        "is_reply": True
                    }
                    print(f"↩️ Reply fetched: {reply_data['text']} (ID: {reply_data['tweet_id']})")
                    Tweet.objects.update_or_create(
                        tweet_id=reply_data["tweet_id"],
                        defaults=reply_data
                    )
                    all_tweets.append(reply_data)
                    print(f"💬 Saved Reply {reply['id']} to Tweet {t['id']}")

                time.sleep(2)  # Delay between tweets to avoid rate limits

        # Add cached tweets to export
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
                "is_reply": ct.is_reply
            })

        # Save JSON and CSV
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

        json_url = os.path.join(settings.MEDIA_URL, json_filename)
        csv_url = os.path.join(settings.MEDIA_URL, csv_filename)

        return render(request, "download_links.html", {
            "json_url": json_url,
            "csv_url": csv_url,
            "count": len(all_tweets)
        })

    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)
