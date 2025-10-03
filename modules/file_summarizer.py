# modules/file_summarizer.py

import PyPDF2
import os
from modules.ai_engine import ask_lily
from modules.tts_output import speak

def read_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        speak("Error reading PDF.")
        return None

def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        speak("Error reading text file.")
        return None

def summarize_selected_file():
    from tkinter import Tk, filedialog
    root = Tk()
    root.withdraw()

    speak("Please select a file to summarize.")
    file_path = filedialog.askopenfilename(
        title="Select a PDF or TXT file",
        filetypes=[("PDF Files", "*.pdf"), ("Text Files", "*.txt")]
    )

    if not file_path:
        speak("No file was selected.")
        return

    if file_path.endswith(".pdf"):
        text = read_pdf(file_path)
    elif file_path.endswith(".txt"):
        text = read_txt(file_path)
    else:
        speak("Only PDF and TXT files are supported for now.")
        return

    if not text:
        speak("Couldn't read the file.")
        return

    if len(text) > 5000:
        text = text[:5000] + "..."

    # 🌟 Ask user to choose summary style
    print("\nChoose summary style:\n[1] Short\n[2] Bullet Points\n[3] Detailed")
    speak("How would you like me to summarize the file? Type 1 for short summary, 2 for bullet points, or 3 for detailed summary.")
    
    choice = input("Your choice (1/2/3): ").strip()

    # 🌟 Create prompt based on user choice
    if choice == "1":
        prompt = f"Summarize the following content briefly:\n{text}"
    elif choice == "2":
        prompt = f"Summarize the following content in bullet points:\n{text}"
    elif choice == "3":
        prompt = f"Write a detailed summary of the following content:\n{text}"
    else:
        speak("Invalid choice. I'll give a short summary.")
        prompt = f"Summarize the following content briefly:\n{text}"

    # 🔁 Send to AI
    summary = ask_lily(prompt)

    if summary:
        speak("Here's the summary:")
        print("\n--- Summary ---\n")
        speak(summary)
    else:
        speak("Couldn't generate a summary.")
