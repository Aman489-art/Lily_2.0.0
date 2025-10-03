import threading
import signal
import sys

# Global interrupt flag
_interrupt_flag = False
_interrupt_lock = threading.Lock()

def set_interrupt_flag():
    """Set the interrupt flag"""
    global _interrupt_flag
    with _interrupt_lock:
        _interrupt_flag = True
        print("\n🛑 Interrupt signal received!")

def reset_interrupt_flag():
    """Reset the interrupt flag"""
    global _interrupt_flag
    with _interrupt_lock:
        _interrupt_flag = False

def get_interrupt_flag():
    """Get the current state of interrupt flag"""
    global _interrupt_flag
    with _interrupt_lock:
        return _interrupt_flag

# Keyboard interrupt listener
def keyboard_interrupt_listener():
    """Listen for keyboard interrupts in a separate thread"""
    from pynput import keyboard
    
    def on_press(key):
        try:
            # Check for Ctrl+Shift+C or specific key combination for interrupt
            if hasattr(key, 'char') and key.char == '\x03':  # Ctrl+C
                set_interrupt_flag()
        except AttributeError:
            pass
    
    def on_release(key):
        # Optional: Add key release handling if needed
        pass
    
    # Start keyboard listener
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release, suppress=False) as listener:
            listener.join()
    except Exception as e:
        print(f"⚠️ Keyboard listener error: {e}")

def start_interrupt_listeners(keyboard_only=True):
    """Start interrupt listeners in background threads"""
    if keyboard_only:
        # Start keyboard listener thread
        keyboard_thread = threading.Thread(target=keyboard_interrupt_listener, daemon=True)
        keyboard_thread.start()
        print("✓ Keyboard interrupt listener started")
    
    # Note: We don't override signal handlers to allow normal Ctrl+C to work
    print("✓ Interrupt handlers initialized")

# Optional: Function to handle graceful shutdown
def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🔄 Received shutdown signal")
    set_interrupt_flag()
    # Don't exit immediately, let main loop handle it
    # sys.exit(0)

# Register signal handlers (optional, can be enabled if needed)
def register_signal_handlers():
    """Register signal handlers for graceful shutdown"""
    # Commented out to allow normal Ctrl+C behavior
    # signal.signal(signal.SIGINT, handle_shutdown)
    # signal.signal(signal.SIGTERM, handle_shutdown)
    pass