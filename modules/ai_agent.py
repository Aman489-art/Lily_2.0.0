import subprocess
import re
import os
import datetime
import json
from modules.ai_engine import ask_lily
from modules.tts_output import speak
from modules.voice_input import listen_for_command
from modules.history_manager import *
from modules.emotion_analyser import get_sentiment

HISTORY_FILE = "data/chat_history.json"
COMMAND_HISTORY_FILE = "data/command_history.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def load_persona():
    """Load the Lily persona configuration"""
    try:
        with open("lily_prompt.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def load_chat_history():
    """Load previous chat history from JSON file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        return []
    except json.JSONDecodeError:
        print("Warning: Chat history file is corrupted. Starting fresh.")
        return []
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []

def save_chat_history(history):
    """Save chat history to JSON file"""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def load_command_history():
    """Load previous command execution history from JSON file"""
    try:
        if os.path.exists(COMMAND_HISTORY_FILE):
            with open(COMMAND_HISTORY_FILE, "r") as f:
                return json.load(f)
        return []
    except json.JSONDecodeError:
        print("Warning: Command history file is corrupted. Starting fresh.")
        return []
    except Exception as e:
        print(f"Error loading command history: {e}")
        return []

def save_command_history(history):
    """Save command execution history to JSON file"""
    try:
        with open(COMMAND_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving command history: {e}")



def log_chat(user_message, ai_response):
    """Log general chat conversations to JSON"""
    mood = get_sentiment(user_message)
    
    # Load existing history
    chat_history = load_chat_history()
    
    # Create new chat entry
    chat_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "ai_response": ai_response,
        "mood": mood
    }
    
    chat_history.append(chat_entry)
    
    # Keep only last 200 chat entries
    if len(chat_history) > 200:
        chat_history = chat_history[-200:]
    
    save_chat_history(chat_history)
    
    # Also save to history manager if it exists
    try:
        save_to_history(user_message, ai_response, mood)
    except:
        pass

def get_recent_chat_context(last_n=5):
    """Get recent chat messages for context"""
    chat_history = load_chat_history()
    if not chat_history:
        return ""
    
    recent_chats = chat_history[-last_n:]
    context_lines = []
    
    for chat in recent_chats:
        context_lines.append(f"User: {chat['user_message']}")
        context_lines.append(f"Lily: {chat['ai_response']}")
    
    return "\n".join(context_lines)

# REPLACE the old get_recent_command_context with this one
def get_recent_command_context(last_n=5):
    """Get recent command executions from the new unified log format for context."""
    command_history = load_command_history()
    if not command_history:
        return ""
    
    recent_entries = command_history[-last_n:]
    context_lines = []
    
    for entry in recent_entries:
        # Safely get all parts of the new log entry
        query = entry.get('user_query', 'N/A')
        attempt = entry.get('attempt', 'N/A')
        command = entry.get('command_executed', 'N/A')
        status = entry.get('status', 'UNKNOWN')
        summary = entry.get('summary', 'No summary.')
        
        context_lines.append(f"Task: \"{query}\" (Attempt {attempt})")
        context_lines.append(f"Command: `{command}`")
        context_lines.append(f"Result: {status} - {summary}")
        context_lines.append("-" * 10) # Separator for clarity
    
    return "\n".join(context_lines)

def get_system_info():
    """Gather system information for AI context"""
    info = {
        'os': subprocess.getoutput('uname -a'),
        'desktop': os.environ.get('XDG_CURRENT_DESKTOP', 'unknown'),
        'shell': os.environ.get('SHELL', 'unknown'),
        'user': os.environ.get('USER', 'unknown'),
        'home': os.path.expanduser('~'),
        'installed_packages': subprocess.getoutput('which apt dpkg yum pacman 2>/dev/null | head -1'),
    }
    return info

# ADD THIS NEW UNIFIED FUNCTION
def log_execution_attempt(user_query, attempt_num, explanation, command, analysis, output):
    """Logs a single command execution attempt with full context to the JSON history."""
    command_history = load_command_history()

    # Create a comprehensive log entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "attempt": attempt_num,
        "strategy": explanation,
        "command_executed": command,
        "status": analysis.get('status', 'UNKNOWN'),
        "summary": analysis.get('summary', 'No summary available.'),
        "issues": analysis.get('issues', 'Not analyzed.'),
        "output": output[:1000] if output else "No output." # Store more output
    }
    
    command_history.append(entry)
    
    # Keep the history file from growing too large
    if len(command_history) > 100:
        command_history = command_history[-100:]
    
    save_command_history(command_history)


def is_system_task_request(user_query):
    """Use AI to determine if it's a system task"""
    detection_prompt = f"""
Analyze this user request: "{user_query}"

Is this a system/technical task that requires Linux commands, or general conversation?

Respond with only: SYSTEM or CHAT
    """
    
    response = ask_lily(detection_prompt).strip().upper()
    return "SYSTEM" in response

def is_safe_command(cmd):
    """Use AI to assess command safety"""
    safety_prompt = f"""
Analyze this Linux command for safety: "{cmd}"

Is this command safe to execute? Consider:
- Destructive operations (rm -rf, format, etc.)
- System modifications that could break things
- Security risks

Respond with only: SAFE or UNSAFE
    """
    
    response = ask_lily(safety_prompt).strip().upper()
    return "SAFE" in response

def analyze_command_execution(command, output, exit_code=None, is_gui_app=False):
    """Use AI to deeply analyze command execution results"""
    
    analysis_prompt = f"""
You are Lily, an expert system administrator analyzing command execution results.

COMMAND EXECUTED: "{command}"
OUTPUT RECEIVED: "{output}"
EXIT CODE: {exit_code if exit_code is not None else "Unknown"}
IS GUI APPLICATION: {is_gui_app}

Analyze this execution and provide detailed insights:

IMPORTANT CONTEXT FOR GUI APPLICATIONS:
- GUI applications (like qv4l2, guvcview, cheese, vlc, firefox) are SUPPOSED to keep running
- If a GUI app is still running (no exit code or exit code 0), this is SUCCESS
- GUI apps often produce minimal or no stdout/stderr when successful
- "Timeout" for GUI apps usually means they launched successfully and are running
- Only consider GUI apps failed if they exit immediately with error code

1. EXECUTION STATUS: Did the command execute successfully?
2. WHAT HAPPENED: What actually occurred during execution?
3. RESULTS: What was accomplished or what failed?
4. ISSUES: Any problems, warnings, or errors detected?
5. NEXT STEPS: What should happen next (if anything)?

Provide your analysis in this format:
STATUS: [SUCCESS/PARTIAL/FAILED]
SUMMARY: [Brief summary of what happened]
DETAILS: [Detailed explanation of the execution]
ISSUES: [Any problems found, or "None detected"]
RECOMMENDATION: [What to do next, or "Task completed"]
    """
    
    analysis = ask_lily(analysis_prompt)
    
    # Parse the analysis
    status_match = re.search(r'STATUS:\s*([^\n]+)', analysis)
    summary_match = re.search(r'SUMMARY:\s*([^\n]+)', analysis)
    details_match = re.search(r'DETAILS:\s*(.+?)(?=ISSUES:|$)', analysis, re.DOTALL)
    issues_match = re.search(r'ISSUES:\s*(.+?)(?=RECOMMENDATION:|$)', analysis, re.DOTALL)
    recommendation_match = re.search(r'RECOMMENDATION:\s*(.+)', analysis, re.DOTALL)
    
    return {
        'status': status_match.group(1).strip() if status_match else 'UNKNOWN',
        'summary': summary_match.group(1).strip() if summary_match else 'Command executed',
        'details': details_match.group(1).strip() if details_match else 'No details available',
        'issues': issues_match.group(1).strip() if issues_match else 'None detected',
        'recommendation': recommendation_match.group(1).strip() if recommendation_match else 'Continue'
    }

def is_gui_application_command(command):
    """Use AI to intelligently detect if a command launches a GUI application"""
    
    gui_detection_prompt = f"""
Analyze this Linux command to determine if it launches a GUI application:

COMMAND: "{command}"

Consider:
- Does this command typically launch a graphical user interface?
- Would this application have windows, buttons, visual interface?
- Is this a desktop application vs command-line tool?
- Would a user interact with this through a GUI?

Examples of GUI apps: web browsers, media players, image viewers, text editors with GUI, file managers, camera apps, games
Examples of CLI apps: grep, ls, cat, apt, systemctl, curl, wget, ssh, vim (terminal version)

Some apps can be both (like vlc can be GUI or CLI depending on parameters).

Respond with only: GUI or CLI
    """
    
    response = ask_lily(gui_detection_prompt).strip().upper()
    return "GUI" in response

def execute_command_with_analysis(command, use_sudo=False):
    """Execute command with comprehensive analysis and feedback"""
    
    print(f"Executing: {command}")
    
    if use_sudo:
        speak("Please enter your system password in the terminal.")
        full_command = f"sudo -S bash -c \"{command}\""
    else:
        full_command = command

    try:
        import subprocess as sp
        
        # Check if this is a GUI application
        is_gui_app = is_gui_application_command(command)
        
        if is_gui_app:
            # For GUI apps, launch them in background and don't wait
            speak("🖥️ Launching GUI application...")
            
            # Launch GUI app in background
            process = sp.Popen(full_command, shell=True, 
                             stdout=sp.PIPE, stderr=sp.PIPE, 
                             text=True, start_new_session=True)
            
            # Give it a moment to start
            import time
            time.sleep(3)
            
            # Check if process is still running (success) or has exited (failure)
            poll_result = process.poll()
            
            if poll_result is None:
                # Process is still running - this is success for GUI apps
                stdout = f"GUI application launched successfully (PID: {process.pid})"
                stderr = ""
                exit_code = 0
                print("✅ Application launched successfully and is running!")
            else:
                # Process exited quickly - might be an error
                stdout, stderr = process.communicate()
                exit_code = poll_result
                if exit_code != 0:
                    print("⚠️ Application started but may have encountered issues.")
        else:
            # For non-GUI commands, use normal execution with timeout
            process = sp.run(full_command, shell=True, capture_output=True, 
                           text=True, timeout=30)
            
            stdout = process.stdout
            stderr = process.stderr  
            exit_code = process.returncode
        
        # Combine output for analysis
        combined_output = ""
        if stdout.strip():
            combined_output += f"STDOUT: {stdout}\n"
        if stderr.strip():
            combined_output += f"STDERR: {stderr}\n"
        if not stdout.strip() and not stderr.strip():
            combined_output = "No output produced"
            
        # Analyze the execution results
        analysis = analyze_command_execution(command, combined_output, exit_code, is_gui_app)
        
        # Provide intelligent feedback based on analysis
        print(f"Command analysis: {analysis['summary']}")
        
        if analysis['status'] == 'SUCCESS':
            if is_gui_app:
                speak("🎉 Application is running! You can use it now.")
            else:
                print("✅ Task completed successfully!")
            if analysis['details'] and 'no details' not in analysis['details'].lower():
                print(f"Details: {analysis['details'][:100]}...")
        
        elif analysis['status'] == 'PARTIAL':
            speak("⚠️ Task partially completed with some issues.")
            print(f"What happened: {analysis['details'][:100]}...")
            if analysis['issues'] and 'none' not in analysis['issues'].lower():
                print(f"Issues found: {analysis['issues'][:100]}...")
        
        else:  # FAILED
            speak("❌ Command execution encountered problems.")
            print(f"Problem: {analysis['details'][:100]}...")
            if analysis['issues'] and 'none' not in analysis['issues'].lower():
                print(f"Specific issues: {analysis['issues'][:100]}...")
        
        # Show relevant output to user (but not for successful GUI apps)
        if not (is_gui_app and analysis['status'] == 'SUCCESS'):
            if stdout.strip():
                print("\n📋 Output:\n")
                speak(f"{stdout[:500]}")
            if stderr.strip():
                print(f"\n⚠️ Errors/Warnings:\n{stderr[:300]}")
        
        return analysis, combined_output, exit_code == 0
        
    except sp.TimeoutExpired:
        error_msg = "Command timed out after 30 seconds"
        print(f"⏰ {error_msg}")
        return {'status': 'FAILED', 'summary': error_msg, 'details': error_msg, 
                'issues': 'Timeout', 'recommendation': 'Try a simpler approach'}, error_msg, False
        
    except Exception as e:
        error_msg = f"Execution error: {str(e)}"
        print(f"💥 {error_msg}")
        return {'status': 'FAILED', 'summary': error_msg, 'details': error_msg,
                'issues': str(e), 'recommendation': 'Try alternative command'}, error_msg, False


def should_retry_based_on_analysis(analysis):
    """Determine if we should retry based on AI analysis"""
    retry_prompt = f"""
Based on this command execution analysis:

STATUS: {analysis['status']}
DETAILS: {analysis['details']}
ISSUES: {analysis['issues']}
RECOMMENDATION: {analysis['recommendation']}

Should we attempt a retry with a different approach?

Consider:
- If it's a complete success, no retry needed
- If it's a failure due to missing software, we could try installing it
- If it's a permission issue, we could try with sudo
- If it's wrong approach, we should try different method
- If it's partial success, we might try to complete the remaining part

Respond with: RETRY or CONTINUE
    """
    
    response = ask_lily(retry_prompt).strip().upper()
    return "RETRY" in response

def intelligent_problem_solver(user_query, failed_attempts=None, max_attempts=3):
    """Let AI handle ALL problem-solving without hardcoding"""
    
    if failed_attempts is None:
        failed_attempts = []
    
    if len(failed_attempts) >= max_attempts:
        speak("I've tried multiple approaches but couldn't solve this completely.")
        return None
    
    # Get current system context
    system_info = get_system_info()
    
    # Get recent command context for learning
    recent_commands = get_recent_command_context()
    
    # Build comprehensive problem-solving prompt
    problem_solving_prompt = f"""
You are Lily, an expert Linux system administrator and problem solver.

USER REQUEST: "{user_query}"

SYSTEM CONTEXT:
- OS: {system_info['os']}
- Desktop Environment: {system_info['desktop']}  
- Shell: {system_info['shell']}
- Home Directory: {system_info['home']}
- Package Manager: {system_info['installed_packages']}

RECENT COMMAND HISTORY:
{recent_commands if recent_commands else "No recent commands"}

PREVIOUS ATTEMPTS: {failed_attempts if failed_attempts else "None - this is the first attempt"}

Your job:
1. Understand what the user wants to accomplish
2. Consider the system environment and context
3. If previous attempts failed, learn from those failures
4. Provide a working solution that fits the user's system
5. Think step-by-step and be creative with alternatives

IMPORTANT RULES:
- Provide ONLY raw commands without markdown formatting
- Consider the actual desktop environment detected
- Be adaptive - don't assume specific software is installed
- Learn from previous failures to try different approaches
- Focus on the end goal, not specific methods

IMPORTANT CONTEXT:
- If this is a GUI application that's still running, that's usually SUCCESS
- GUI applications often produce minimal output when successful
- CLI tools typically complete quickly and exit
- Long-running processes might be services or GUI apps
- Exit code 0 usually means success, non-zero usually means error

For GUI applications specifically:
- If still running (no exit code or exit code 0), this is likely SUCCESS
- If exited immediately with error, this is FAILED
- Minimal stdout/stderr is normal for GUI apps

For CLI applications:
- Should complete and exit normally
- Output content is important for determining success
- Exit codes are reliable indicators

CRITICAL: Keep commands simple! For GUI apps, just run the app directly:
- Good: "cheese" or "guvcview" 
- Bad: "sudo apt update && sudo apt install -y cheese && cheese"

Return format:
Explanation: (Brief explanation of your approach)
Command: (Single working command - keep it simple!)

If software needs installation, suggest that as a separate step first.
    """
    
    response = ask_lily(problem_solving_prompt)
    
    # Extract explanation and command
    explanation_match = re.search(r"Explanation:\s*(.+?)(?=Command:|$)", response, re.DOTALL)
    command_match = re.search(r"Command:\s*(.+)", response, re.DOTALL)
    
    explanation = explanation_match.group(1).strip() if explanation_match else "Attempting to solve the task"
    command = command_match.group(1).strip() if command_match else None
    
    if not command:
        return None
        
    # Clean up command formatting
    command = re.sub(r'```\w*\n?', '', command)
    command = re.sub(r'```', '', command) 
    command = ' '.join(command.split())
    command = command.replace('`', '')
    
    return explanation, command

# REPLACE the old execute_with_ai_retry with this one
def execute_with_ai_retry(user_query):
    """Execute commands with AI analysis and retry logic, using a unified logger."""
    failed_attempts = []
    max_attempts = 3
    
    for attempt in range(max_attempts):
        current_attempt_num = attempt + 1
        print(f"🔄 Attempt {current_attempt_num} of {max_attempts}")
        
        explanation = "No explanation generated."
        command = "No command generated."
        analysis = {}
        output = ""
        
        try:
            # Get AI solution
            result = intelligent_problem_solver(user_query, failed_attempts)
            if not result:
                speak("I couldn't devise a command for this task.")
                # Log this failure to devise a plan
                analysis = {'status': 'FAILED', 'summary': 'AI could not generate a command.'}
                log_execution_attempt(user_query, current_attempt_num, "Planning Failed", "N/A", analysis, "")
                continue

            explanation, command = result
            
            if not is_safe_command(command):
                speak("🛡️ The suggested command might be unsafe. I'll try a different approach.")
                failure_reason = f"Unsafe command blocked: {command}"
                failed_attempts.append(f"Attempt {current_attempt_num}: {failure_reason}")
                analysis = {'status': 'FAILED', 'summary': failure_reason}
                log_execution_attempt(user_query, current_attempt_num, explanation, command, analysis, "")
                continue
            
            print(f"💡 Strategy: {explanation}")
            
            needs_sudo = "sudo" in command.lower()
            analysis, output, _ = execute_command_with_analysis(command, use_sudo=needs_sudo)
            
            # ALWAYS LOG THE ATTEMPT
            log_execution_attempt(user_query, current_attempt_num, explanation, command, analysis, output)

            if analysis.get('status') == 'SUCCESS':
                print("🎉 Perfect! Task accomplished successfully.")
                return True
                
            # Add failure details for the next attempt's context
            failure_details = f"Command: `{command}`, Status: {analysis.get('status')}, Issues: {analysis.get('issues')}, Output: {output[:200]}"
            failed_attempts.append(f"Attempt {current_attempt_num}: {failure_details}")
            
            if current_attempt_num < max_attempts:
                print("🔄 Analyzing the result and trying a different approach...")

        except Exception as e:
            error_details = f"An unexpected error occurred: {str(e)}"
            print(f"💥 {error_details}")
            failed_attempts.append(f"Attempt {current_attempt_num}: {error_details}")
            # Log the exception
            analysis = {'status': 'FAILED', 'summary': 'An exception occurred during execution.', 'issues': str(e)}
            log_execution_attempt(user_query, current_attempt_num, explanation, command, analysis, "")
            continue
    
    speak("😔 I tried multiple approaches but couldn't fully accomplish the task.")
    return False

def get_execution_summary():
    """Provide a summary of recent command executions"""
    try:
        command_history = load_command_history()
        if not command_history:
            return "No execution history available yet."
        
        recent_commands = command_history[-10:]
        
        summary_prompt = f"""
Analyze these recent command execution logs and provide a brief summary:

{json.dumps(recent_commands, indent=2)}

Focus on:
- How many commands were executed recently
- Success vs failure rate
- Common issues encountered
- Overall system health

Keep response under 100 words.
        """
        
        summary = ask_lily(summary_prompt)
        return summary
        
    except Exception as e:
        return f"Could not analyze execution history: {str(e)}"

def handle_system_task(user_query):
    """Handle system tasks using pure AI intelligence with comprehensive feedback"""
    print("🧠 Analyzing your request and planning the best approach...")
    
    # Show system context awareness
    system_info = get_system_info()
    print(f"Working on {system_info['desktop']} desktop environment...")
    
    success = execute_with_ai_retry(user_query)
    
    if success:
        print("✨ All done! Is there anything else you'd like me to help with?")
    else:
        speak("🤔 I wasn't able to complete that task fully.")
        print("Would you like me to:")
        print("1. Try a different approach")
        print("2. Explain what went wrong") 
        print("3. Suggest alternative solutions")

def handle_general_chat(user_query):
    """Handle general conversation with context from previous chats"""
    
    # Load persona
    persona = load_persona()
    
    # Get recent chat context
    context = get_recent_chat_context(last_n=5)
    
    # Build chat prompt with persona and context
    chat_prompt = f"""
{json.dumps(persona, indent=2) if persona else "You are Lily, a friendly AI assistant."}

RECENT CONVERSATION HISTORY:
{context if context else "This is the start of the conversation."}

User just said: "{user_query}"

Respond naturally as Lily, taking into account the conversation history and your persona.
Keep your response conversational and human-like.
    """
    
    response = ask_lily(chat_prompt)
    speak(response)
    log_chat(user_query, response)
    return response

def handle_user_input(user_query, user_mood=None, context=""):
    """Main function to route user input intelligently"""
    if not user_query or user_query.strip() == "":
        speak("I didn't catch that. Could you repeat?")
        return

    # Use AI to determine the type of request
    if is_system_task_request(user_query):
        handle_system_task(user_query)
    else:
        handle_general_chat(user_query)

def show_history_stats():
    """Display statistics about chat and command history"""
    chat_history = load_chat_history()
    command_history = load_command_history()
    
    print("\n" + "="*50)
    print("📊 HISTORY STATISTICS")
    print("="*50)
    print(f"Total chats recorded: {len(chat_history)}")
    print(f"Total commands executed: {len(command_history)}")
    
    if chat_history:
        latest_chat = chat_history[-1]
        print(f"Last chat: {latest_chat['timestamp']}")
    
    if command_history:
        latest_command = command_history[-1]
        print(f"Last command: {latest_command['timestamp']}")
        
        # Calculate success rate
        successful = sum(1 for cmd in command_history if cmd.get('status') == 'SUCCESS')
        if command_history:
            success_rate = (successful / len(command_history)) * 100
            print(f"Command success rate: {success_rate:.1f}%")
    
    print("="*50 + "\n")