from django import forms
from .models import TweetURL

class TweetURLForm(forms.ModelForm):
    class Meta:
        model = TweetURL
        fields = ['url', 'category']

