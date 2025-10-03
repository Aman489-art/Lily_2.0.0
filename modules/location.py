import json
import subprocess
import requests
import os
import time
from dotenv import load_dotenv
from modules.tts_output import speak

load_dotenv()
location_path = os.getenv("LOCATION_PATH")

# Typing animation effect
def typing_effect(text, delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

# Get GPS location via Termux (SSH)
def get_gps_from_termux():
    try:
        speak("📡 Trying to get GPS location from your phone...")
        ssh_cmd = location_path
        output = subprocess.check_output(ssh_cmd, shell=True, text=True).strip()

        if not output:
            speak("⚠️ No response from Server.")
            return None, None

        data = json.loads(output)
        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat and lon:
            print(f"✅ Coordinates from GPS: {lat}, {lon}")
            return lat, lon
        else:
            print("⚠️ GPS data incomplete.")
            return None, None

    except Exception as e:
        speak(f"⚠️ GPS fetch failed: {e}")
        return None, None

# Get fallback IP-based location via ipinfo
def get_location_from_ipinfo():
    try:
        typing_effect("🌐 Falling back to IP-based location...")
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()

        loc = data.get("loc")  # "lat,lon"
        city = data.get("city")
        country = data.get("country")
        region = data.get("region")

        if loc:
            lat, lon = map(float, loc.split(","))
            speak(f"✅ Coordinates from IP: {lat}, {lon}")
            return lat, lon, f"{city}, {region}, {country}"
        else:
            print("⚠️ IP location missing.")
            return None, None, "Unknown city"
    except Exception as e:
        speak(f"⚠️ IP-based location fetch failed: {e}")
        return None, None, "Unknown location"

# Reverse geocode lat/lon to address
def reverse_geocode(lat, lon):
    try:
        typing_effect("🔍 Searching your location on the map...")
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'Lily-Assistant'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        add = data.get("display_name", "Unknown address")
        speak(f"You are currently in : {add}")
    except Exception as e:
        print(f"⚠️ Reverse geocoding failed: {e}")
        return "Unknown address"

# Main callable function
def get_location_summary():
    lat, lon = get_gps_from_termux()

    if lat and lon:
        address = reverse_geocode(lat, lon)
        return f"📍 You are currently near:\n{address}\n📌 (Lat: {lat}, Lon: {lon})"
    
    # Fallback to IP-based location
    lat, lon, rough_location = get_location_from_ipinfo()
    if lat and lon:
        address = reverse_geocode(lat, lon)
        return f"📍 I couldn't access GPS, but based on your IP, you're somewhere near:\n{address}\n📌 (Lat: {lat}, Lon: {lon})"
    
    return "😔 I couldn't fetch your location at the moment. Let's try again later."

