import os
from datetime import datetime
from modules.tts_output import speak
#import pyautogui
import time
import subprocess 
from modules.music_player import search_youtube_music, play_music_from_url
import psutil 
import brightnessctl
import re 
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
# Import the functions from your reminder system
from modules.reminder_tasks import (
    set_timer
)

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def handle_music_command():
    speak("What song do you want to play?")
    query = input("🎶 What song do you want to play? ").strip()
    if not query:
        print("⚠️ No song name provided.")
        return True

    results = search_youtube_music(query)
    if not results:
        print("❌ No results found.")
        return True

    print("\n🎧 Search Results:")
    for i, item in enumerate(results):
        print(f"{i+1}. {item['title']}")

    choice = input("\nSelect a song number: ").strip()
    if not choice.isdigit():
        print("⚠️ Invalid input.")
        return True

    choice = int(choice) - 1
    if 0 <= choice < len(results):
        video_url = f"https://www.youtube.com/watch?v={results[choice]['id']}"
        play_music_from_url(video_url)
    else:
        print("⚠️ Number out of range.")

    return True

def parse_time_string(time_str):
    try:
        now = datetime.now()
        if "am" in time_str.lower() or "pm" in time_str.lower():
            remind_time = datetime.strptime(time_str, "%I:%M %p")
            return now.replace(hour=remind_time.hour, minute=remind_time.minute, second=0, microsecond=0)
        elif ":" in time_str:
            remind_time = datetime.strptime(time_str, "%H:%M")
            return now.replace(hour=remind_time.hour, minute=remind_time.minute, second=0, microsecond=0)
        else:
            # "6 am" → try adding :00
            time_str += ":00"
            remind_time = datetime.strptime(time_str, "%I:%M %p")
            return now.replace(hour=remind_time.hour, minute=remind_time.minute, second=0, microsecond=0)
    except:
        return None

def get_ip_location():

    try:
        response = requests.get('https://ipinfo.io/json')
        response.raise_for_status()
        data = response.json()
        #print(data)
        ip = data.get('ip')
        city = data.get('city')
        region = data.get('region')
        country = data.get('country')
        location = data.get('loc')
        speak(f"You are in {city} city of {region} state in {country}")
        speak(f"Your location address is {location}")
        speak(f"Your ip address is {ip}")


        
        # Return city with country for better context
        if city and country:
            return f"{city}, {country}"
        return city
        
    except requests.RequestException as e:
        print(f"⚠️ IP-based location detection failed: {e}")
        return None
    except json.JSONDecodeError:
        speak("⚠️ Invalid response from location service")
        return None

def wiki_search(query):
    import wikipedia
    wikipedia.set_lang("en")
    try:
        results = wikipedia.search(query)
        if results:
            summary = wikipedia.summary(results[0], sentences=3)
            return summary
        else:
            return "No results found."
    except wikipedia.exceptions.DisambiguationError as e:
        return "Your search is ambiguous. Try being more specific."
    except wikipedia.exceptions.PageError:
        return "The page was not found on Wikipedia."
    except Exception as e:
        return f"Error: {e}"

def news():

    # Your NewsAPI key

    API_KEY = os.getenv("NEWS_API")


    # Base URL for top headlines
    url = 'https://newsapi.org/v2/top-headlines'

    # Combine national and international sources or countries
    params = {
        'apiKey': API_KEY,
        'language': 'en',
        'pageSize': 10,  # You can increase for more results
    }

    # You can also filter by country (e.g. 'in' for India, 'us' for USA)
    # For mixed national + international, we do two requests

    def fetch_news(country=None):
        if country:
            params['country'] = country
        else:
            params.pop('country', None)  # Remove country for global search

        response = requests.get(url, params=params)
        data = response.json()

        if data.get('status') != 'ok':
            return f"❌ Error: {data.get('message', 'Unknown error')}"
        articles = data.get('articles', [])
        
        if not articles:
            return "⚠️ No news articles found."
            
        for i, article in enumerate(data['articles'], 1):
            speak(f"\n{i}. {article['title']}")
            print(f"   📰 Source: {article['source']['name']}")
            print(f"   🔗 URL: {article['url']}")
            speak(f"   📝 {article['description']}\n")


    # Fetch Indian (national) news
    speak("🇮🇳 National News (India):")
    fetch_news(country='in')

    # Fetch Global (international) news
    speak("\n🌐 International News:")
    fetch_news()  # no country = global news

