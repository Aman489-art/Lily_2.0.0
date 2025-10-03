import json
import os
from datetime import datetime

MEMORY_FILE = "lily_memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as file:
        return json.load(file)

def save_important_point(text, source="lily"):
    memory = load_memory()
    memory.append({
        "text": text.strip(),
        "source": source,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=4)

def show_memory():
    memory = load_memory()
    if not memory:
        return "No saved memories yet."
    return "\n\n".join([f"[{m['time']}] {m['source'].capitalize()}: {m['text']}" for m in memory])
