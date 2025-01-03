import re
import time
import requests
from pathlib import Path


# For configuration and setup help, see README.md.


try:
    from config import *
except ImportError:
    print("Please create a config.py file with your settings!")
    print("See config.example.py for a template.")
    exit(1)


# Regular expression pattern for trade messages
TRADE_PATTERN = r'(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}).*@From ([^:]+): Hi, I would like to buy your (.*?) listed for (.*?) in ([^(]+) \(stash tab "(.*?)"; position: left (\d+), top (\d+)\)'

def parse_trade_message(message):
    """Extract trade information from message using regex"""
    match = re.search(TRADE_PATTERN, message)
    if match:
        return {
            'date': match.group(1),          # New!
            'time': match.group(2),          # New!
            'buyer_name': match.group(3),    # Note: group numbers shifted
            'item_name': match.group(4),
            'item_cost': match.group(5),
            'league': match.group(6).strip(),
            'tab_name': match.group(7),
            'left': match.group(8),
            'top': match.group(9)
        }
    return None

def tail_file(file_path):
    """Generator function to tail a file similar to Unix 'tail -f'"""
    print("Starting to tail file...")  # Debug print
    with open(file_path, 'r', encoding='utf-8') as file:
        print("File opened successfully")  # Debug print
        # First, read and discard existing content
        file.seek(0, 2)
        print("Seeked to end of file")  # Debug print
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line.strip()

def send_to_home_assistant(trade_data):
    """Send trade data to Home Assistant"""
    # Add the player name to the trade data
    trade_data['player_name'] = PLAYER_NAME
    
    url = f"http://{HA_ADDRESS}/api/events/{HA_EVENT}"
    headers = {
        "Authorization": f"Bearer {HA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=trade_data)
        response.raise_for_status()
        print(f"Successfully sent trade notification for {trade_data['item_name']}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Home Assistant: {e}")
        

def main():
    log_path = Path(LOG_FILE)
    print("Starting script...")  # Debug print
    
    if not log_path.exists():
        print(f"Error: Log file not found at {LOG_FILE}")
        return
    
    print("File found!")  # Debug print
    print(f"Monitoring {LOG_FILE} for trade messages...")
    
    try:  # Add try/except to catch any file reading errors
        for line in tail_file(LOG_FILE):
            print(f"Read line: {line[:50]}...")  # Debug print first 50 chars
            trade_data = parse_trade_message(line)
            if trade_data:
                print(f"Trade request detected for {trade_data['item_name']}")
                send_to_home_assistant(trade_data)
    except Exception as e:
        print(f"Error while reading file: {e}")

if __name__ == "__main__":
    main()