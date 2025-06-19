from django import forms
from .models import TweetURL
import re

class TweetURLForm(forms.ModelForm):
    class Meta:
        model = TweetURL
        fields = ['url', 'category']
        widgets = {
            'url': forms.URLInput(attrs={
                'placeholder': 'Paste tweet URL here...',
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_url(self):
        url = self.cleaned_data.get('url')

        # Accept both twitter.com and x.com URLs
        tweet_url_pattern = re.compile(r"^https?://(www\.)?(twitter\.com|x\.com)/\w+/status/\d+$")
        if not tweet_url_pattern.match(url):
            raise forms.ValidationError(
                "❌ Invalid tweet or X URL format. Example: https://x.com/user/status/1234567890"
            )

        if TweetURL.objects.filter(url=url).exists():
            raise forms.ValidationError("⚠️ This tweet/X URL already exists.")

        return url
