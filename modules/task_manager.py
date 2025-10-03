# modules/task_manager.py

import json
import os
from datetime import datetime
from modules.tts_output import speak

TASK_FILE = "data/tasks.json"

def load_tasks():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(TASK_FILE):
        with open(TASK_FILE, "w") as f:
            json.dump([], f)
    with open(TASK_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

def add_task(description, date_str=None):
    tasks = load_tasks()
    task = {
        "description": description,
        "date": date_str or datetime.now().strftime("%Y-%m-%d")
    }
    tasks.append(task)
    save_tasks(tasks)
    speak(f"Task added: {description}")

def view_tasks():
    tasks = load_tasks()
    if not tasks:
        speak("Your task list is empty.")
        return
    speak("Here are your tasks:")
    for i, task in enumerate(tasks, 1):
        speak(f"{i}. {task['description']} on {task['date']}")

def delete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        save_tasks(tasks)
        speak(f"Deleted task: {removed['description']}")
    else:
        speak("Invalid task number.")
