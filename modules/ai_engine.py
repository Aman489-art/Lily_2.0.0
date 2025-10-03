from modules.config import GEMINI_API_KEY
import json
import google.generativeai as genai
import time
import re 
from pathlib import Path


genai.configure(api_key=GEMINI_API_KEY)

# Define models
PRIMARY_MODEL = "gemini-2.0-flash-exp"
FALLBACK_MODEL = "gemini-2.5-flash-lite"

# Cooldown settings (in seconds)
COOLDOWN_DURATION = 60  # You can change to 120 for 2 minutes, etc.
last_failure_time = 0  # Timestamp of last failure
last_model_used = "PRIMARY"  # For optional logging
cooldown_until = 0  # UNIX timestamp until primary is on cooldown

# Load system prompt from this module's directory (works locally and on servers)
PROMPT_PATH = Path(__file__).resolve().parent / "lily_prompt.json"
def load_lily_prompt():
    with open(PROMPT_PATH, "r") as file:
        prompt_data = json.load(file)

    full_prompt = prompt_data["persona"] + "\n\n"
    for section in prompt_data:
        if section == "persona":
            continue
        elif isinstance(prompt_data[section], list):
            full_prompt += "\n".join(prompt_data[section]) + "\n\n"

    return full_prompt.strip()

lily_system_prompt = load_lily_prompt()

# Create chat session
def create_chat(model_name):
    model = genai.GenerativeModel(model_name)
    return model.start_chat(history=[{"role": "user", "parts": [lily_system_prompt]}])

# Initialize chat sessions
primary_chat = create_chat(PRIMARY_MODEL)
fallback_chat = create_chat(FALLBACK_MODEL)

def parse_retry_after_seconds(error_message: str) -> int:
    """
    Extracts retry duration from Gemini error messages like:
    'Rate limit exceeded. Try again in 45 seconds.'
    """
    match = re.search(r"(\d+)\s*seconds", error_message.lower())
    if match:
        return int(match.group(1))
    return 60  # Default fallback if no number found

def ask_lily(prompt: str) -> str:
    global last_failure_time
    prompt = prompt.strip()
    if not prompt:
        return ""

    now = time.time()
    in_cooldown = now - last_failure_time < COOLDOWN_DURATION

    # Decide which model to use
    if not in_cooldown:
        try:
            response = primary_chat.send_message(prompt)
            reply = response.text.strip()
            if reply:

                if last_model_used != "PRIMARY":
                    print("✅ Primary model is back online.")
                    last_model_used = "PRIMARY"
                return reply
            else:
                raise Exception("Empty reply from primary model.")
        except Exception as e:
            error_message = str(e)
            retry_after = parse_retry_after_seconds(error_message)
            cooldown_until = time.time() + retry_after
            #print(f"⚠️ Primary model failed. Cooldown activated for {retry_after} seconds.")
            last_model_used = "FALLBACK"

    # Fallback execution
    try:
        response = fallback_chat.send_message(prompt)
        reply = response.text.strip()
        if reply:
            if last_model_used != "FALLBACK":
                print("🔁 Using fallback model.")
                last_model_used = "FALLBACK"
            return reply
        else:
            return "I'm having trouble answering right now. Please try again later."
    except Exception:
        print("❌ Fallback model also failed.")
        return "Sorry, I couldn't respond due to temporary issues."
