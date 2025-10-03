import subprocess
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
phone_ssh = os.getenv("SSH_CODE")

# ✅ Fetch contacts as a list (not string)
def get_contacts():
    try:
        cmd = f"{phone_ssh} termux-contact-list"
        output = subprocess.check_output(cmd, shell=True, text=True)
        contacts = json.loads(output)
        return contacts  # Return the raw list

    except Exception as e:
        print("⚠️ Failed to fetch contacts:", e)
        return []

# 📋 Show all contacts with numbers (clean text)
def list_contact_numbers():
    contacts = get_contacts()

    if not contacts:
        return "Your contact list is empty."

    contact_text = "📇 Here are your contacts:\n"
    for idx, contact in enumerate(contacts, 1):
        name = contact.get("name", "Unknown")
        numbers = contact.get("number") or contact.get("numbers") or []
        if isinstance(numbers, str):
            numbers = [numbers]
        for num in numbers:
            contact_text += f"{idx}. {name} - {num}\n"

    return contact_text.strip()

# 🔍 Search by name
def search_contact_by_name(name):
    contacts = get_contacts()
    for contact in contacts:
        if name.lower() in contact.get('name', '').lower():
            return contact
    return None

# 🔍 Search by number
def search_contact_by_number(number):
    contacts = get_contacts()
    for contact in contacts:
        numbers = contact.get("number") or contact.get("numbers") or []
        if isinstance(numbers, str):
            numbers = [numbers]
        for num in numbers:
            if number in num:
                return contact
    return None

# 📞 Make call
def make_call(number):
    try:
        cmd = f"{phone_ssh} termux-telephony-call {number}"
        subprocess.run(cmd, shell=True)
        print(f"📞 Calling {number}...")
        return True
    except Exception as e:
        print("⚠️ Failed to make call:", e)
        return False

# 🧠 Full interactive call flow
def call_contact_interactive(query=None):
    while True:
        if query:
            match = re.search(r"call (.+)", query)
            if match:
                name = match.group(1).strip()
                contact = search_contact_by_name(name)
                if contact:
                    number = contact.get("number") or (contact.get("numbers")[0] if contact.get("numbers") else None)
                    if number:
                        make_call(number)
                        return f"📞 Calling {contact['name']} at {number}"
                else:
                    speak(f"Couldn't find {name}. Want to try by name or number?")
                    query = None
                    continue

        speak("Do you want to call by name or number?")
        mode = listen_for_command().strip().lower()

        if "name" in mode:
            speak("Please say the contact name.")
            name = listen_for_command()
            contact = search_contact_by_name(name)
            if contact:
                number = contact.get("number") or (contact.get("numbers")[0] if contact.get("numbers") else None)
                if number:
                    make_call(number)
                    return f"📞 Calling {contact['name']} at {number}"
            speak(f"No contact found with the name {name}. Let's try again.")
            continue

        elif "number" in mode:
            speak("Please say the phone number.")
            number = input("Enter number : ")
            if make_call(number):
                return f"📞 Calling {number}"
            else:
                speak("Something went wrong. Let's try again.")
                continue

        else:
            speak("Sorry, I didn’t get that. Please say 'name' or 'number'.")

