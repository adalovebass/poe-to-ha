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
        trade_data = {
            'sending_player_name': PLAYER_NAME,
            'date': match.group(1),
            'time': match.group(2),
            'buyer_player_name': match.group(3),
            'item_name': match.group(4),
            'item_cost': match.group(5),
            'league': match.group(6).strip(),
            'tab_name': match.group(7),
            'left': match.group(8),
            'top': match.group(9)
        }

        print(f"Trade request detected ({trade_data['item_cost']}for {trade_data['item_name']})")
        send_to_home_assistant("poe_trade_incoming", trade_data)

        return True
    return False

# This set is populated with other player names who join your area, so we can ignore death/level messages for them.
other_area_members = set()

AREA_JOINED_PATTERN = r'(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}).*\[INFO Client \d+\] : ([^\\]+) has joined the area\.'

def parse_join_message(message):
    match = re.search(AREA_JOINED_PATTERN, message)
    if match:
        username = match.group(3)
        other_area_members.add(username)
        print(f"Added {username} to 'other area members': {other_area_members}")
        return True
    return False


AREA_LEFT_PATTERN = r'(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}).*\[INFO Client \d+\] : ([^\\]+) has left the area\.'

def parse_left_message(message):
    match = re.search(AREA_LEFT_PATTERN, message)
    if match:
        username = match.group(3)
        other_area_members.discard(username)  # discard() won't raise error if not present
        print(f"Removed {username} from 'other area members': {other_area_members}")
        return True
    return False


LEVEL_UP_PATTERN = r'(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}).*\[INFO Client \d+\] : ([^\s]+) \(([^)]+)\) is now level \d+'

def parse_level_up_message(message):
    level_match = re.search(LEVEL_UP_PATTERN, message)
    if level_match:
        data = {
            'sending_player_name': PLAYER_NAME,
            'date': level_match.group(1),
            'time': level_match.group(2),
            'leveled_player_name': level_match.group(3),
            'class_name': level_match.group(4)
        }

        if data['leveled_player_name'] not in other_area_members:
            print(f"Detected level event for us")
            send_to_home_assistant("poe_player_leveled", data)
            return True
        else:
            print(f"Detected level event for another party member.")
    return False


DEATH_PATTERN = r'(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2}).*\[INFO Client \d+\] : ([^\s]+) has been slain\.'

def parse_death_message(message):
    death_match = re.search(DEATH_PATTERN, message)
    if death_match:
        data = {
            'sending_player_name': PLAYER_NAME,
            'date': death_match.group(1),
            'time': death_match.group(2),
            'dead_player_name': death_match.group(3)
        }

        if data['dead_player_name'] not in other_area_members:
            send_to_home_assistant("poe_player_died", data)
            print(f"Detected death event for us")
            return True
        else:
            print(f"Detected death event for another party member.")
    return False


def tail_file(file_path):
    """Generator function to tail a file similar to Unix 'tail -f'"""
    print("Starting to tail file...")  # Debug print
    with open(file_path, 'r', encoding='utf-8') as file:
        print("File opened successfully")

        # First, read and discard existing content
        file.seek(0, 2)
        print("Seeked to end of file, beginning tail")  # Debug print

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line.strip()

def send_to_home_assistant(event_name, data):
    """Send event and data to Home Assistant"""
    
    url = f"http://{HA_ADDRESS}/api/events/{event_name}"
    headers = {
        "Authorization": f"Bearer {HA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Successfully sent {event_name} notification with data: {data}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Home Assistant: {e}")


def main():
    log_path = Path(LOG_FILE)
    print("Starting script...")

    print(f"Player name is {PLAYER_NAME}")
    
    if not log_path.exists():
        print(f"Error: Log file not found at {LOG_FILE}")
        return
    
    print("File found!")  # Debug print
    print(f"Monitoring {LOG_FILE} for trade messages...")
    
    try:  # Add try/except to catch any file reading errors
        for line in tail_file(LOG_FILE):

            if DEBUG:
                print(f"Read line: {line[:76]}...")  # Debug print first n chars
            
            if (parse_trade_message(line)):
                continue
            if (parse_join_message(line)):
                continue
            if (parse_left_message(line)):
                continue
            if (parse_death_message(line)):
                continue
            if (parse_level_up_message(line)):
                continue

    except Exception as e:
        print(f"Error while reading file: {e}")
        exit(1)

if __name__ == "__main__":
    main()