# import os
# import pandas as pd
# from pathlib import Path
# from textblob import TextBlob
# from django.conf import settings
# from xhtml2pdf import pisa
# from django.template.loader import render_to_string

# def clean_text(text):
#     return text.encode('ascii', errors='ignore').decode('utf-8', errors='ignore')

# def analyze_sentiment(text):
#     try:
#         cleaned = clean_text(text)
#         blob = TextBlob(cleaned)
#         polarity = blob.sentiment.polarity
#         if polarity > 0:
#             return 'Positive'
#         elif polarity < 0:
#             return 'Negative'
#         else:
#             return 'Neutral'
#     except Exception as e:
#         return 'Error'

# def process_all_csvs():
#     media_dir = Path(settings.MEDIA_ROOT)
#     result_files = []

#     for file in media_dir.glob("*_tweets.csv"):
#         df = pd.read_csv(file)
#         if 'text' not in df.columns:
#             continue

#         df['sentiment'] = df['text'].astype(str).apply(analyze_sentiment)

#         base_name = file.stem.replace("_tweets", "")
#         sentiment_csv_name = f"{base_name}_sentiment.csv"
#         sentiment_html_name = f"{base_name}_sentiment.html"
#         sentiment_pdf_name = f"{base_name}_sentiment.pdf"

#         sentiment_csv_path = media_dir / sentiment_csv_name
#         sentiment_html_path = media_dir / sentiment_html_name
#         sentiment_pdf_path = media_dir / sentiment_pdf_name

#         # Save CSV
#         df.to_csv(sentiment_csv_path, index=False)

#         # Generate HTML
#         html_content = render_to_string("sentiment_template.html", {
#             "category": base_name,
#             "tweets": df.to_dict(orient="records")
#         })

#         # Save HTML
#         with open(sentiment_html_path, "w", encoding="utf-8") as f:
#             f.write(html_content)

#         # Generate PDF
#         with open(sentiment_pdf_path, "wb") as f:
#             pisa.CreatePDF(html_content, dest=f)

#         result_files.append({
#             "csv_name": sentiment_csv_name,
#             "html_name": sentiment_html_name,
#             "pdf_name": sentiment_pdf_name
#         })

#     return result_files
