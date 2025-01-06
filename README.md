# PoE Trade Notifier for Home Assistant

This script monitors your Path of Exile log file for various events and sends them to Home Assistant for notifications and automation.

## Requirements

- Python 3.6 or newer
- Home Assistant instance
- Path of Exile 2 (Beta)

## Installation

1. Install Python 3.6+ from [python.org](https://python.org) if you haven't already
2. Clone the repository:
   ```bash
   git clone https://github.com/adalovebass/poe-to-ha
   ```
    Alternatively, you can download the .zip of the repository from [https://github.com/adalovebass/poe-to-ha]()
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `config.example.py` to `config.py` and edit with your settings

## Configuration

### Home Assistant Setup

1. Generate a Long-Lived Access Token in Home Assistant, if you don't have one:
   - Click your user profile (bottom left)
   - Click "Security" along the top
   - Scroll to "Long Lived Access Tokens"
   - Click "Create Token"
   - Give it a name (e.g., "POE Trade", or your PC's name)
   - Copy the token for copying into config.py (you won't see this code from HA again!)

2. Update `config.py` with your settings:
   - `PLAYER_NAME`: Your name (will appear as `sending_player_name` in all events)
   - `HA_API_KEY`: Your Long-Lived Access Token
   - `HA_ADDRESS`: Your Home Assistant address (e.g., "192.168.1.100:8123")
   - `LOG_FILE`: Path to your PoE Client.txt
     - Steam: "C:/Program Files (x86)/Steam/steamapps/common/Path of Exile 2/logs/Client.txt"
     - Standalone: "C:/Program Files (x86)/Grinding Gear Games/Path of Exile 2/logs/Client.txt"
   - `DEBUG`: Set to True for verbose logging (optional)

## Usage

1. Run the script with:
    ```bash
    python -u ha_poe.py
    ```
    (-u runs the script without stdout buffering, otherwise you may not see stdout output right away)
2. Launch the game as normaal.

The script will:
1. Monitor your PoE log file for various events
2. Parse out relevant details
3. Send this data to Home Assistant
4. Trigger any automations you've set up

## Available Event Data

Each event type provides different data fields under `trigger.event.data`. Note that `sending_player_name`, `date`, and `time` are included in all events.

### poe_trade_incoming
Trigger:
```yaml
trigger:
  - trigger: event
    event_type: poe_trade_incoming
```
Available data:
- `sending_player_name`: Your name (from config)
- `date`: Date of event
- `time`: Time of event
- `buyer_player_name`: Name of the player wanting to buy
- `item_name`: The item they want to buy
- `item_cost`: Listed price
- `league`: Which league (Standard, etc)
- `tab_name`: Stash tab name
- `left`: Left position in stash tab
- `top`: Top position in stash tab

### poe_player_leveled
Only triggers for your character (filtered from party members).

Trigger:
```yaml
trigger:
  - trigger: event
    event_type: poe_player_leveled
```
Available data:
- `sending_player_name`: Your name (from config)
- `date`: Date of event
- `time`: Time of event
- `leveled_player_name`: Character name from log
- `class_name`: Character class
- `level`: New level

### poe_player_died
Only triggers for your character (filtered from party members).

Trigger:
```yaml
trigger:
  - trigger: event
    event_type: poe_player_died
```
Available data:
- `sending_player_name`: Your name (from config)
- `date`: Date of event
- `time`: Time of event
- `dead_player_name`: Character name from log

## Example Automation

Here's a sample automation that put an entry in the Event Log and flashes a light red when a trade request comes in:

```yaml
alias: poe_trade_incoming
description: "Flash light red when trade request received"
triggers:
  - trigger: event
    event_type: poe_trade_incoming
actions:
  - action: logbook.log
    data:
      name: poe_trade_incoming
      message: >-
        {% if trigger is defined and trigger.event is defined and trigger.event.data is defined %}
          [{{ trigger.event.data.date }} {{ trigger.event.data.time }}] {{ trigger.event.data.buyer_player_name }} wants to buy {{ trigger.event.data.item_name }} for {{ trigger.event.data.item_cost }} in {{ trigger.event.data.league }}. Located in tab {{ trigger.event.data.tab_name }} at position left {{ trigger.event.data.left }}, top {{ trigger.event.data.top }}
        {% else %}
          PoE trade automation was run manually
        {% endif %}
  - action: scene.create
    data:
      scene_id: temp_light_state
      snapshot_entities:
        - light.your_light_name  # Replace with your light's entity_id
  - action: light.turn_on
    target:
      entity_id: light.your_light_name  # Replace with your light's entity_id
    data:
      rgb_color: [255, 0, 0]
      transition: 0.2
  - delay:
      seconds: 1
  - action: scene.turn_on
    data:
      transition: 0.2
      entity_id: scene.temp_light_state
mode: single
```