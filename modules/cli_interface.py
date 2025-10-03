import os
import sys
import time

class LilyInterface:
    def __init__(self, version="2.0.0"):
        self.version = version
        self.theme_color = "cyan"
        self.startup_messages = []
        
    def clear_screen(self):
        """Clear the screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print the sticky header - simple ASCII art"""
        # Simplified ASCII art that works in all terminals
        print("=" * 53)
        print("=" + " " * 51 + "=")
        print("=            LILY v2 - AI Voice Assistant           =")
        print("=" + " " * 51 + "=")
        print("=" * 53)

    def print_welcome_banner(self):
        """Print welcome message below header"""
        print("=" * 53)
        print("  Welcome to Lily")
        print("  Your intelligent AI assistant is starting up...")
        print("  Type 'help' for available commands")
        print("=" * 53)

    def print_startup_banner(self):
        """Initial startup - header + welcome"""
        self.clear_screen()
        self.print_header()
        self.print_welcome_banner()

    def refresh_header(self):
        """Refresh just the header at top of screen"""
        self.clear_screen()
        self.print_header()
        self.print_welcome_banner()

    def animate_startup_step(self, message, duration=0.3):
        """Animate a startup step with simple dots"""
        dots = ['   ', '.  ', '.. ', '...']
        steps = int(duration * 4)
        
        for i in range(steps):
            sys.stdout.write(f"\r  {dots[i % len(dots)]} {message}")
            sys.stdout.flush()
            time.sleep(duration / steps)
        
        print(f"\r  [OK] {message}" + " " * 10)
        self.startup_messages.append(message)

    def show_startup_sequence(self):
        """Show animated startup sequence"""
        print("\n[*] System Initialization")
        print("-" * 53)
        
        startup_steps = [
            ("Initializing audio systems", 0.4),
            ("Loading conversation history", 0.3),
            ("Preparing AI models", 0.5),
            ("Calibrating microphone", 0.4),
            ("Loading user preferences", 0.3),
        ]
        
        for step, duration in startup_steps:
            self.animate_startup_step(step, duration)

    def clear_startup_sequence(self):
        """Clear startup messages from screen but keep header"""
        self.clear_screen()
        self.print_header()
        self.print_welcome_banner()

    def show_command_list(self):
        """Display available commands"""
        print("\n[*] Available Commands")
        print("-" * 53)
        commands = [
            ("help", "Show this help message"),
            ("history", "Show conversation history"),
            ("stats", "Display session statistics"),
            ("remember [text]", "Save important information"),
            ("sleep now", "Put Lily in sleep mode"),
            ("wake up lily", "Wake Lily from sleep mode"),
            ("clear", "Clear the screen"),
            ("exit/quit", "Exit the application")
        ]
        for cmd, desc in commands:
            print(f"  {cmd:20} - {desc}")
        print("-" * 53 + "\n")

    def print_status(self, message, status_type="info"):
        """Print a status message with prefix"""
        prefixes = {
            "info": "[i]",
            "success": "[+]",
            "error": "[!]",
            "listening": "[~]",
            "processing": "[*]",
            "speaking": "[>]"
        }
        prefix = prefixes.get(status_type, "[*]")
        print(f"{prefix} {message}")

    def print_user_input(self, text):
        """Print user input"""
        print(f"\n[YOU] {text}")

    def print_lily_response(self, text):
        """Print Lily's response"""
        print(f"[LILY] {text}")

# Global instance
lily_ui = LilyInterface()

def init_interface(version="2.0.0"):
    """Initialize the CLI interface"""
    global lily_ui
    lily_ui = LilyInterface(version)
    return lily_ui

def show_startup():
    """Show startup banner"""
    lily_ui.print_startup_banner()

def show_startup_sequence():
    """Show animated startup sequence"""
    lily_ui.show_startup_sequence()

def clear_startup_sequence():
    """Clear startup sequence and show clean interface"""
    lily_ui.clear_startup_sequence()

def refresh_header():
    """Refresh the header"""
    lily_ui.refresh_header()

def clear_screen():
    """Clear the screen"""
    lily_ui.clear_screen()

def print_header():
    """Print the header"""
    lily_ui.print_header()

def show_command_list():
    """Show available commands"""
    lily_ui.show_command_list()

def print_status(message, status_type="info"):
    """Print status message"""
    lily_ui.print_status(message, status_type)

def print_user_input(text):
    """Print user input"""
    lily_ui.print_user_input(text)

def print_lily_response(text):
    """Print Lily response"""
    lily_ui.print_lily_response(text)