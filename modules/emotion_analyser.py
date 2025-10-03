# modules/emotion_analyzer.py
from textblob import TextBlob

def get_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.5:
        return "very happy"
    elif polarity > 0:
        return "happy"
    elif polarity == 0:
        return "neutral"
    elif polarity > -0.5:
        return "upset"
    else:
        return "very upset"
