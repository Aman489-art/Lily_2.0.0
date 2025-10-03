import os
import sys

# CRITICAL: Set environment variables BEFORE any other imports
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_LOG_SEVERITY_LEVEL'] = 'ERROR'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress ALL warnings
import warnings
warnings.filterwarnings('ignore')

# Redirect stderr to suppress library warnings
original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

# Now safe to import audio libraries
from modules.voice_input import *
from modules.tts_output import speak
from modules.ai_agent import *
from modules.interrupt_handler import *
from modules.error_logger import log_error
import speech_recognition as sr
from threading import Thread
import datetime
import time
import multiprocessing
from modules.interrupt_handler import get_interrupt_flag, reset_interrupt_flag
from modules.ai_agent import handle_user_input, show_history_stats, load_chat_history, load_command_history
from modules.system_startup import startup_greet
from modules.background_loops import start_background_threads
from modules.emotion_analyser import get_sentiment
from modules.history_manager import *
from modules.emotion_voice_engine import *
from modules.handle_command import *

# Import the enhanced CLI interface
from modules.cli_interface import *

# Restore stderr for actual errors we want to see
sys.stderr = original_stderr

# Initialize context history
context_history = ""


def update_context_history():
    """Update context history from both recall_context and new JSON history"""
    global context_history
    try:
        context_history = recall_context(5)
        from modules.ai_agent import get_recent_chat_context
        recent_context = get_recent_chat_context(last_n=3)
        if recent_context:
            context_history = f"{context_history}\n\nRecent conversations:\n{recent_context}"
    except Exception as e:
        log_error(e, context="Context Update", extra="Failed to update context history")
        context_history = ""


def run_task_with_interrupt(query, user_mood):
    """Run AI task with interrupt support and context"""
    update_context_history()
    
    process = multiprocessing.Process(target=handle_user_input, args=(query, user_mood, context_history))
    process.start()

    while process.is_alive():
        if get_interrupt_flag():
            process.terminate()
            process.join()
            print_lily_response("Command stopped.")
            speak("Command stopped.")
            reset_interrupt_flag()
            return
        time.sleep(0.1)
    
    process.join()


def pre_adjust_microphone():
    """Pre-adjust microphone for ambient noise silently"""
    with suppress_stderr():

        try:
            with sr.Microphone(device_index=1) as source:
                recognizer = sr.Recognizer()
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
        except:
            pass


def preload_system_data():
    """Preload system resources with animation"""
    try:
        show_startup_sequence()
        pre_adjust_microphone()
        
        try:
            chat_history = load_chat_history()
            command_history = load_command_history()
            
            if chat_history:
                print(f"  [OK] Loaded {len(chat_history)} previous conversations")
            if command_history:
                print(f"  [OK] Loaded {len(command_history)} command executions")
        except Exception as e:
            log_error(e, context="History Load", extra="Error loading history files")
        
        update_context_history()
        
        print("-" * 53)
        print("  [+] All systems ready!")
        time.sleep(1)
        
    except Exception as e:
        log_error(e, context="System Preload", extra="Error during system initialization")
        print(f"  [!] System initialization error: {str(e)}")


def handle_special_commands(query):
    """Handle special system commands that don't need AI processing"""
    query_lower = query.lower().strip()
    
    if query_lower in ["help", "commands", "what can you do"]:
        show_command_list()
        return True
    
    if query_lower in ["clear", "cls"]:
        clear_screen()
        print_header()
        print_status("Ready! Listening for commands...", "success")
        print("-" * 53)
        return True
    
    if any(cmd in query_lower for cmd in ["show history", "show stats", "history stats", "my history"]):
        try:
            print("\n[*] Session Statistics")
            print("-" * 53)
            show_history_stats()
            speak("Here are your interaction statistics.")
            return True
        except Exception as e:
            log_error(e, context="Show History", extra=f"Query: {query}")
            print_status("Couldn't load history stats right now", "error")
            speak("Sorry, couldn't load history stats right now.")
            return True
    
    if "clear chat history" in query_lower:
        try:
            response = input("[?] Are you sure you want to clear chat history? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                import shutil
                from datetime import datetime
                backup_file = f"data/chat_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    shutil.copy(HISTORY_FILE, backup_file)
                    print(f"[+] Backup created: {backup_file}")
                except:
                    pass
                
                save_chat_history([])
                print_status("Chat history cleared. Backup saved.", "success")
                speak("Chat history cleared. Backup saved.")
            else:
                print_status("Keeping your history", "info")
                speak("Okay, keeping your history.")
            return True
        except Exception as e:
            log_error(e, context="Clear History", extra=f"Query: {query}")
            print_status("Error clearing history", "error")
            return True
    
    return False




def main():
    """Main program loop with clean interface"""
    VERSION = "2.0.0"
    
    # Initialize CLI interface
    init_interface(VERSION)
    
    
    # Preload system data with animation
    preload_system_data()
    
    # Clear startup messages and show clean interface
    clear_startup_sequence()
    
    # Show ready status
    startup_greet()
    print_status("Ready! Listening for commands...", "success")
    print("-" * 53 + "\n")

    lily_sleeping = False

    while True:
        try:
            if get_interrupt_flag():
                print_lily_response("Command stopped.")
                speak("Command stopped.")
                reset_interrupt_flag()
                continue

            if lily_sleeping:
                query = listen_for_command()
                    
                if query and any(kw in query.lower() for kw in ["wake up lily", "hey lily", "lily come back"]):
                    lily_sleeping = False
                    print_status("Waking up...", "success")
                    speak("I'm back! What do you need?")
                    print_lily_response("I'm back! What do you need?")
                    update_context_history()
                continue

            # Listen for command (this handles its own status display)
            query = listen_for_command()
                
            if not query:
                continue

            query = query.strip().lower()
            
            # Display user query
            print_user_input(query)

            if "sleep now" in query:
                speak("Okay, going quiet. Say 'wake up Lily' to wake me.")
                lily_sleeping = True
                print("\n[i] Sleep Mode Active")
                print("    Say 'wake up Lily' to resume...")
                print("-" * 53 + "\n")
                continue

            if any(word in query for word in ["exit", "quit", "stop listening"]):
                try:
                    print("\n[*] Session Summary")
                    print("-" * 53)
                    print(f"  Commands: {len(load_command_history()) if load_command_history() else 0}")
                    print(f"  Conversations: {len(load_chat_history()) if load_chat_history() else 0}")
                    print("-" * 53)
                except:
                    pass
                
                speak("Shutting down. Stay safe!")
                print("\n" + "=" * 53)
                print("  Thank you for using Lily!")
                print("  Stay safe and productive!")
                print("=" * 53 + "\n")
                break

            if "remember" in query:
                try:
                    from modules.lily_memory import save_important_point
                    point = query.replace("remember", "").strip()
                    if point:
                        save_important_point(point, source="user")
                        print_status("Memory saved successfully", "success")
                        speak("Got it. Locked it in.")
                        print_lily_response("Got it. I've locked that in memory.")
                    continue
                except Exception as e:
                    log_error(e, context="Memory Save", extra=f"Query: {query}")
                    print_status("Couldn't save that right now", "error")
                    speak("Sorry, I couldn't save that right now.")
                    continue

            if handle_special_commands(query):
                continue

            command_executed = handle_command(query)

            if not command_executed:
                user_mood = get_sentiment(query)
                print(f"[i] Mood: {user_mood.title()}")
                print_status("Processing...", "processing")
                run_task_with_interrupt(query, user_mood)

            update_context_history()
            print()  # Add spacing

        except KeyboardInterrupt:
            print("\n")
            print_status("Keyboard interrupt detected", "info")
            try:
                response = input("[?] Do you want to exit Lily? (yes/no): ")
                if response.lower() in ['yes', 'y']:
                    speak("Shutting down. Stay safe!")
                    print("\n" + "=" * 53)
                    print("  Thank you for using Lily!")
                    print("  Stay safe and productive!")
                    print("=" * 53 + "\n")
                    break
                else:
                    print_status("Continuing...", "info")
                    speak("Continuing...")
                    continue
            except KeyboardInterrupt:
                print("\nForcing exit...")
                break
                
        except Exception as e:
            print_status(f"An error occurred: {e}", "error")
            log_error(e, context="Main Loop", extra=f"Query: {query if 'query' in locals() else 'N/A'}")
            speak("Sorry, I encountered an error. Let's try again.")
            
            try:
                update_context_history()
            except:
                pass


def safe_shutdown():
    """Perform safe shutdown operations"""
    try:
        print("\n[*] Shutdown Sequence")
        print("-" * 53)
        
        try:
            print("[i] Saving session data...")
            update_context_history()
        except:
            pass
        
        try:
            show_history_stats()
        except:
            pass
        
        print("[+] Shutdown complete")
        print("-" * 53)
        
    except Exception as e:
        log_error(e, context="Safe Shutdown", extra="Error during shutdown")
        print(f"[!] Shutdown error: {str(e)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Program interrupted by user")
    except Exception as e:
        print(f"[!] Fatal error: {str(e)}")
        log_error(e, context="Program Startup", extra="Fatal error in main")
    finally:
        safe_shutdown()