#!/home/birdman/.venvs/isaac/bin/python3
import os
import subprocess
import sys
import json
import re
import datetime
import readline
from pathlib import Path
from openai import OpenAI # type: ignore
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Config file path
CONFIG_DIR = Path.home() / '.config' / 'isaac'
CONFIG_FILE = CONFIG_DIR / 'config.json'
MONITORED_FOLDERS_FILE = CONFIG_DIR / 'monitored_folders.json'

# History file for readline
HISTORY_READLINE_FILE = Path.home() / '.isaac_history'
MAX_READLINE_HISTORY = 1000

# Default config
DEFAULT_CONFIG = {
    'api_key': None,
    'safe_mode': False,
    'history_enabled': True,
    'max_history': 20,
    'model': 'grok-3',
}

# Global flags and histories
MONITORING_ACTIVE = False
OBSERVER = None
SESSION_HISTORY = []
CHAT_HISTORY = []
HISTORY_FILE = Path.home() / '.isaac_session.jsonl'
AUTOSTART_FILE = Path.home() / '.isaac_autostart'
USER_ROLE = "superuser"  # Default to superuser

def load_config():
    try:
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True)
        if not CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print(f"\033[1;33mCreated default config at {CONFIG_FILE}.\033[0m")
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        sys.exit(1)

config = load_config()
HISTORY_ENABLED = config.get('history_enabled', True)
MAX_HISTORY = config.get('max_history', 20)
CHAT_MODE = False
SAFE_MODE = config.get('safe_mode', False)
JR_MODE = False

api_key = config.get('api_key') or os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: Set API key in config.json or XAI_API_KEY/OPENAI_API_KEY env var.")
    sys.exit(1)

try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    sys.exit(1)

# Load readline history
if HISTORY_READLINE_FILE.exists():
    readline.read_history_file(HISTORY_READLINE_FILE)

INTERACTIVE_COMMANDS = ["mc", "vim", "nano", "less", "top", "htop"]

RISKY_PATTERNS = [
    r'rm\s+-rf',
    r'sudo\s+rm',
    r'dd\s+if=',
]

class FileMonitorHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory:
            print(f"Isaac > File change detected: {event.src_path} ({event.event_type})")

def display_history(limit=5):
    if not SESSION_HISTORY:
        print("Isaac > No command history available.")
        return
    for entry in reversed(SESSION_HISTORY[-limit:]):
        print(f"[{entry['timestamp']}] {entry.get('user_role', 'unknown')}: {entry['input']} -> {entry['corrected_command']}")
        if entry['stdout']:
            print(f"  Output: {entry['stdout'][:100]}...")
        if entry['stderr']:
            print(f"  Error: {entry['stderr'][:100]}...")

def update_monitored_folders(folder_path, purpose):
    global MONITORING_ACTIVE, OBSERVER
    folder_path = os.path.expanduser(folder_path)
    monitored = {}
    if MONITORED_FOLDERS_FILE.exists():
        with open(MONITORED_FOLDERS_FILE, 'r') as f:
            monitored = json.load(f)
    monitored[folder_path] = {
        'purpose': purpose,
        'created': datetime.datetime.now().isoformat(),
        'monitored': True
    }
    with open(MONITORED_FOLDERS_FILE, 'w') as f:
        json.dump(monitored, f, indent=4)
    
    if not MONITORING_ACTIVE:
        try:
            OBSERVER = Observer()
            OBSERVER.schedule(FileMonitorHandler(), folder_path, recursive=True)
            OBSERVER.start()
            MONITORING_ACTIVE = True
            print(f"Isaac > Started monitoring {folder_path} for {purpose}.")
        except Exception as e:
            print(f"Isaac > Monitoring error: {str(e)}")
    else:
        print(f"Isaac > Monitoring already active; added {folder_path} to tracked folders.")

def check_folder(folder_path):
    folder_path = os.path.expanduser(folder_path)
    if os.path.exists(folder_path):
        print(f"Isaac > Folder {folder_path} exists.")
    else:
        print(f"Isaac > Folder {folder_path} does not exist.")

def check_package(package):
    stdout, stderr, rc = execute_command(f"dpkg -l | grep {package}")
    if rc == 0 and stdout:
        print(f"Isaac > Package {package} is installed.")
    else:
        print(f"Isaac > Package {package} is not installed.")

def suggest_alternative(alt_command, purpose):
    print(f"Isaac > Suggested alternative: {alt_command} ({purpose})")

def log_monitoring(folder_path, purpose):
    folder_path = os.path.expanduser(folder_path)
    monitored = {}
    if MONITORED_FOLDERS_FILE.exists():
        with open(MONITORED_FOLDERS_FILE, 'r') as f:
            monitored = json.load(f)
    if folder_path not in monitored:
        monitored[folder_path] = {
            'purpose': purpose,
            'created': datetime.datetime.now().isoformat(),
            'monitored': True
        }
        with open(MONITORED_FOLDERS_FILE, 'w') as f:
            json.dump(monitored, f, indent=4)
        print(f"Isaac > Added {folder_path} to monitored folders for {purpose}.")

def get_ai_response(prompt, context=""):
    history_summary = "Recent commands and outcomes:\n" + "\n".join([f"[{e['timestamp']}] {e.get('user_role', 'unknown')}: {e['input']} -> {e['corrected_command']} (Output: {e['stdout'][:100]}{'...' if len(e['stdout']) > 100 else ''}, Error: {e['stderr'][:100]}{'...' if len(e['stderr']) > 100 else ''})" for e in SESSION_HISTORY[-3:]]) if SESSION_HISTORY else "No recent commands."
    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": f"""You are Isaac, an Intelligent Shell Assistant. User role: {USER_ROLE}. Validate commands, correct typos, and handle natural language for tasks like folder creation/monitoring. For natural queries (e.g., 'where to save images? Create folder'), suggest a safe location (e.g., ~/Images), generate commands (e.g., mkdir), and include actions to log to ~/.config/isaac/monitored_folders.json. For follow-up questions (e.g., 'what did you do?'), use context to explain recent actions. For 'dmidecode' commands, always suggest using 'sudo'. If a command fails due to 'command not found', check if the package is installed before suggesting installation. Return JSON: {{'valid': bool, 'command': str or list, 'message': str, 'actions': list of dicts for db/json updates}}. For actions like update_json, use 'path' and 'purpose' in data keys."""},
                {"role": "user", "content": f"Analyze: {prompt}\nContext: {context}\nSession context: {history_summary}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"valid": False, "command": prompt, "message": f"Error in AI response: {str(e)}"})

def get_ai_chat_response(user_input):
    global CHAT_HISTORY
    history_summary = "Recent chat context:\n" + "\n".join([f"[{e['timestamp']}] {e.get('user_role', 'unknown')}: {e['input']}\nResponse: {e['response'][:200]}..." for e in CHAT_HISTORY[-5:]]) if CHAT_HISTORY else "No recent chat history."
    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": f"You are Isaac in chat mode, a conversational shell assistant. User role: {USER_ROLE}. Answer naturally and avoid executing commands unless explicitly requested. For queries implying commands (e.g., 'what time is it?'), suggest a command (e.g., 'date') in your response."},
                {"role": "user", "content": f"User input: {user_input}\nContext: {history_summary}"}
            ],
            max_tokens=300
        )
        chat_response = response.choices[0].message.content
        CHAT_HISTORY.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'input': user_input,
            'response': chat_response,
            'user_role': USER_ROLE
        })
        return chat_response
    except Exception as e:
        return f"Error in chat response: {str(e)}"

def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

def is_risky_command(cmd):
    for pattern in RISKY_PATTERNS:
        if re.search(pattern, cmd):
            return True
    return False

def normalize_json(response):
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    return response.strip()

def invoke_other_agent(agent_name, command):
    print(f"Isaac > Invoking {agent_name} agent with command: {command}")

def get_prompt_dir():
    cwd = os.getcwd()
    home = str(Path.home())
    if cwd.startswith(home):
        return "~" + cwd[len(home):]
    return cwd

def display_help():
    help_text = """
Isaac - Intelligent Shell Assistant
Usage:
  isaac [command]         Execute natural language or shell commands
  isaac -chat             Enter chat mode
  isaac -sarah [cmd]      Invoke Sarah agent
  history                 Show recent command history
  history show [N]        Show last N commands
  help                    Show this help
  exit/quit               Exit Isaac
"""
    print(help_text)

def main():
    global CHAT_MODE, JR_MODE, USER_ROLE, SAFE_MODE

    parser = argparse.ArgumentParser(description="Isaac - Intelligent Shell Assistant")
    parser.add_argument("-start", action="store_true", help="Start in JR mode")
    parser.add_argument("-chat", action="store_true", help="Start in chat mode")
    parser.add_argument("-sarah", type=str, help="Invoke Sarah agent")
    parser.add_argument("command", nargs="*", help="Command to execute")

    args = parser.parse_args()

    if args.command:
        prompt = " ".join(args.command)
        ai_response = get_ai_response(prompt)
        ai_response = normalize_json(ai_response)
        try:
            data = json.loads(ai_response)
            valid = data.get("valid", False)
            corrected_command = data.get("command", prompt)
            message = data.get("message", "")
            actions = data.get("actions", [])

            print(f"Isaac > {message}")
            if isinstance(corrected_command, list):
                commands = corrected_command
            elif corrected_command:
                commands = [corrected_command]
            else:
                commands = []

            if valid and commands:
                for cmd in commands:
                    if SAFE_MODE and is_risky_command(cmd):
                        confirm = input("Risky cmd, confirm? (y/n): ")
                        if confirm.lower() != "y":
                            continue
                    stdout, stderr, returncode = execute_command(cmd)
                    print(stdout)
                    if stderr:
                        print(f"\033[1;31m{stderr}\033[0m")

            for action in actions:
                if action.get('type') == 'update_json':
                    update_monitored_folders(action['data']['path'], action['data']['purpose'])

            if HISTORY_ENABLED:
                entry = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'input': prompt,
                    'corrected_command': corrected_command,
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': returncode,
                    'message': message,
                    'actions': actions,
                    'user_role': USER_ROLE
                }
                SESSION_HISTORY.append(entry)
                if len(SESSION_HISTORY) > MAX_HISTORY:
                    SESSION_HISTORY.pop(0)
                with open(HISTORY_FILE, 'a') as f:
                    f.write(json.dumps(entry) + '\n')

                if returncode == 0 and corrected_command:
                    readline.add_history(prompt)
                    readline.write_history_file(HISTORY_READLINE_FILE)
        except:
            print("Error parsing response.")
        sys.exit(0)

    if args.start or args.chat or (AUTOSTART_FILE.exists() and not any(vars(args).values())):
        JR_MODE = True if args.start else False
        CHAT_MODE = args.chat

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            SESSION_HISTORY.extend([json.loads(line) for line in f if line.strip()])
        SESSION_HISTORY = SESSION_HISTORY[-MAX_HISTORY:]

    print("\033[1;36mIsaac active.\033[0m")
    print("Isaac > Use 'isaac [command]' or natural language queries to ensure validation and logging.")

    try:
        while True:
            prompt_prefix = "[jr]" if JR_MODE and not CHAT_MODE else "[cm]" if CHAT_MODE else ""
            prompt_dir = get_prompt_dir()
            command = input(f"\033[1;32m┌─{prompt_prefix}[birdman@parrot]─[{prompt_dir}]\n└──╼ $ \033[0m ").strip()

            if not command:
                continue

            if command.lower() in ["exit", "quit"]:
                if CHAT_MODE:
                    CHAT_MODE = False
                    JR_MODE = True
                    CHAT_HISTORY = []  # Clear chat history on exit
                    print("Isaac > Returning to shell mode.")
                    continue
                if MONITORING_ACTIVE and OBSERVER:
                    OBSERVER.stop()
                    OBSERVER.join()
                    print("Isaac > Stopped file monitoring.")
                readline.write_history_file(HISTORY_READLINE_FILE)
                print("Isaac > Goodbye!")
                break

            if command.lower() == "help":
                display_help()
                continue

            if command.lower() in ["history", "isaac -history"]:
                display_history()
                continue
            if command.lower().startswith("history show"):
                parts = command.split()
                limit = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5
                display_history(limit)
                continue

            if command.startswith("isaac -sarah "):
                USER_ROLE = "sarah"
                invoke_other_agent("Sarah", command.split("isaac -sarah ")[1])
                continue

            if command == "isaac -chat":
                CHAT_MODE = True
                JR_MODE = False
                CHAT_HISTORY = []  # Clear chat history on entry
                print("Isaac > you are now in chat mode, terminal commands will NOT work, type 'quit' or 'exit' to leave.")
                continue

            if CHAT_MODE:
                chat_response = get_ai_chat_response(command)
                print(f"Isaac > {chat_response}")
                continue

            ai_response = get_ai_response(command)
            ai_response = normalize_json(ai_response)
            stdout = ""
            stderr = ""
            returncode = 0
            try:
                data = json.loads(ai_response)
                valid = data.get("valid", False)
                corrected_command = data.get("command", command)
                message = data.get("message", "")
                actions = data.get("actions", [])

                print(f"Isaac > {message}")
                if isinstance(corrected_command, list):
                    commands = corrected_command
                    for cmd in commands:
                        print(f"Action > {cmd}")
                elif corrected_command:
                    commands = [corrected_command]
                    print(f"Action > {corrected_command}")
                else:
                    commands = []

                if valid and commands:
                    for cmd in commands:
                        if SAFE_MODE and is_risky_command(cmd):
                            confirm = input("Risky cmd, confirm? (y/n): ")
                            if confirm.lower() != "y":
                                continue
                        stdout, stderr, returncode = execute_command(cmd)
                        print(stdout)
                        if stderr:
                            print(f"\033[1;31m{stderr}\033[0m")
                        if returncode != 0:
                            error_resp = get_ai_response(f"Analyze error: {stderr}", cmd)
                            error_data = json.loads(normalize_json(error_resp))
                            print(f"Isaac > {error_data.get('message', 'Error analyzing response')}")
                            if error_data.get('command'):
                                print(f"Action > {error_data['command']}")

                        if cmd.startswith("cd "):
                            try:
                                os.chdir(os.path.expanduser(cmd.split("cd ")[1].strip()))
                            except Exception as e:
                                print(f"Dir error: {e}")

                for action in actions:
                    print(f"Isaac > Action: {action}")
                    if action.get('type') == 'update_json' and action.get('file') == '~/.config/isaac/monitored_folders.json':
                        update_monitored_folders(action['data']['path'], action['data']['purpose'])
                    elif action.get('type') == 'check_folder':
                        check_folder(action['path'])
                    elif action.get('type') == 'log_monitoring' and action.get('file') == '~/.config/isaac/monitored_folders.json':
                        log_monitoring(action['entry']['folder'], action['entry']['purpose'])
                    elif action.get('type') == 'check_package':
                        check_package(action['data']['package'])
                    elif action.get('type') == 'suggest_alternative':
                        suggest_alternative(action['data']['alternative_command'], action['data']['purpose'])

            except json.JSONDecodeError:
                print("Isaac > Invalid response.")
                valid = False
                corrected_command = ""
                message = ""
                actions = []
                commands = []

            if HISTORY_ENABLED:
                entry = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'input': command,
                    'corrected_command': corrected_command,
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': returncode,
                    'message': message,
                    'actions': actions,
                    'user_role': USER_ROLE
                }
                SESSION_HISTORY.append(entry)
                if len(SESSION_HISTORY) > MAX_HISTORY:
                    SESSION_HISTORY.pop(0)
                with open(HISTORY_FILE, 'a') as f:
                    f.write(json.dumps(entry) + '\n')

                if returncode == 0 and corrected_command:
                    readline.add_history(command)
                    readline.write_history_file(HISTORY_READLINE_FILE)

    finally:
        if MONITORING_ACTIVE and OBSERVER:
            OBSERVER.stop()
            OBSERVER.join()
            print("Isaac > Stopped file monitoring.")

if __name__ == "__main__":
    main()
