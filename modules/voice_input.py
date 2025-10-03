import os
import sys
import speech_recognition as sr
from contextlib import contextmanager

# ==============================
# SYSTEM UTILS
# ==============================
@contextmanager
def suppress_stderr():
    try:
        if not sys.__stderr__:
            yield
            return
        fd = sys.__stderr__.fileno()
        dup_fd = os.dup(fd)
        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), fd)
        yield
    except Exception as e:
        print(f"⚠️ stderr suppression skipped: {e}")
        yield
    finally:
        try:
            if 'fd' in locals() and 'dup_fd' in locals():
                os.dup2(dup_fd, fd)
                os.close(dup_fd)
        except Exception:
            pass


DEVICE_INDEX = 1

# ==============================
# VOICE RECOGNITION
# ==============================

recognizer = sr.Recognizer()


def listen_for_command():
    """Listen for voice command with clean output - shows only ONE status line"""
    try:
        from modules.interrupt_handler import get_interrupt_flag
    except:
        get_interrupt_flag = lambda: False
    
    audio = None
    
    # Suppress ALL audio library warnings and errors
    with suppress_stderr():
        try:
            with sr.Microphone(device_index=DEVICE_INDEX) as source:
                # Check for interrupt flag
                if get_interrupt_flag():
                    return ""

                # Adjust for ambient noise silently
                recognizer.adjust_for_ambient_noise(source, duration=0.2)

        except KeyboardInterrupt:
            raise
        except Exception:
            return None
    
    # Only NOW show listening status (after all setup is done)
    sys.stdout.write("[~] Listening...")
    sys.stdout.flush()
    
    with suppress_stderr():
        try:
            with sr.Microphone(device_index=DEVICE_INDEX) as source:
                # Listen for audio with timeout
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
                except sr.WaitTimeoutError:
                    # Clear the listening message
                    sys.stdout.write("\r" + " " * 60 + "\r")
                    sys.stdout.flush()
                    return None

        except KeyboardInterrupt:
            # Clear the listening message
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            raise
        except Exception:
            # Clear the listening message
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            return None

    # If no audio captured, return None
    if audio is None:
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()
        return None

    # Change status to recognizing
    sys.stdout.write("\r[*] Recognizing..." + " " * 40)
    sys.stdout.flush()

    # Recognition phase
    with suppress_stderr():
        try:
            text = recognizer.recognize_google(audio)
            # Clear the status line completely
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            return text.lower()
        except sr.UnknownValueError:
            # Clear the status line
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            return None
        except sr.RequestError as e:
            # Clear the status line
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            print(f"[!] API error: {e}")
            return None
        except KeyboardInterrupt:
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            raise