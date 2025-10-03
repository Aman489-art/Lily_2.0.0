import requests
import os
from dotenv import load_dotenv
from modules.location import get_gps_from_termux, get_location_from_ipinfo
from modules.tts_output import speak
load_dotenv()
api_key = os.getenv("OPENWEATHER_API")

def get_weather(lat, lon):
    try:
        speak("🌤️ Fetching weather data...")
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code != 200 or 'main' not in data:
            print("⚠️ Failed to get weather data:", data.get("message", "Unknown error"))
            return "I couldn't fetch the weather info right now."

        # Extract relevant weather data
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        description = data['weather'][0]['description'].capitalize()
        wind = data['wind']['speed']
        humidity = data['main']['humidity']
        city = data['name']

        # Format nicely
        weather_report = (
            f"🌍 Weather in {city}:\n"
            f"🌡️ Temperature: {temp}°C (feels like {feels_like}°C)\n"
            f"🌤️ Condition: {description}\n"
            f"💨 Wind Speed: {wind} m/s\n"
            f"💧 Humidity: {humidity}%"
        )
        speak("Here is the weather report in your location")
        speak(weather_report)

    except Exception as e:
        print(f"⚠️ Error fetching weather: {e}")
        return "Something went wrong while getting the weather."

# Wrapper for Lily: Get weather using current GPS or IP-based location
def get_weather_report():
    lat, lon = get_gps_from_termux()
    if not lat or not lon:
        lat, lon, _ = get_location_from_ipinfo()
    
    if lat and lon:
        return get_weather(lat, lon)
    else:
        return "❌ Unable to get location for weather lookup."

