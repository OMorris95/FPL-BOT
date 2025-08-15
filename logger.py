from datetime import datetime

LOG_FILE = "fpl_bot_log.txt"

def log_action(message):
    """Appends a timestamped message to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"❌ Failed to write to log file: {e}")

def get_last_logged_gameweek():
    """Reads the log file to find the last gameweek summary that was logged."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            if "Gameweek Summary for GW" in line:
                # Extracts the gameweek number from a line like '[...] Gameweek Summary for GW8:'
                return int(line.split("GW")[1].split(':')[0])
        return 0 # No gameweek has been logged yet
    except FileNotFoundError:
        return 0 # Log file doesn't exist yet