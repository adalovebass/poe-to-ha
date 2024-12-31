# PoE Trade Notifier for Home Assistant

This script monitors your Path of Exile log file for incoming trade requests and sends them to Home Assistant for notifications and automation.

## Requirements

- Python 3.6 or newer
- Home Assistant instance
- Path of Exile installed (Steam or Standalone)

## Installation

1. Install Python 3.6+ from [python.org](https://python.org) if you haven't already
2. Download these files:
   - `poe_trade_notification.py`
   - `config.example.py`
   - `requirements.txt`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `config.example.py` to `config.py` and edit with your settings

## Configuration

### Home Assistant Setup

1. Generate a Long-Lived Access Token in Home Assistant:
   - Click your user profile (bottom left)
   - Click "Security" along the top
   - Scroll to "Long Lived Access Tokens"
   - Click "Create Token"
   - Give it a name (e.g., "POE Trade", or your PC's name)
   - Copy the token (you won't see it again!)

2. Update `config.py` with your settings:
   - `HA_API_KEY`: Your Long-Lived Access Token
   - `HA_ADDRESS`: Your Home Assistant address (e.g., "192.168.1.100:8123")
   - `HA_EVENT`: Event name for automations (default: "poe_trade_incoming")
   - `LOG_FILE`: Path to your PoE Client.txt
     - Steam: "C:/Program Files (x86)/Steam/steamapps/common/Path of Exile 2/logs/Client.txt"
     - Standalone: "C:/Program Files (x86)/Grinding Gear Games/Path of Exile 2/logs/Client.txt"

### Home Assistant Automation Example

Here's a sample automation that flashes lights when a trade request comes in. Be sure to replace "light.your_light_name" with your light's name.
It also outputs a message to the event log, as a demontsration of using the various data properties available in the event.

```yaml
alias: poe_trade_incoming_sample
description: "Sample automation to flash a light red when a trade comes in"
triggers:
  - trigger: event
    event_type: poe_trade_incoming
actions:
  - action: logbook.log
    data:
      name: poe_trade_incoming
      message: >-
        {% if trigger is defined and trigger.event is defined and trigger.event.data is defined %}
          [{{ trigger.event.data.date }} {{ trigger.event.data.time }}] {{ trigger.event.data.buyer_name }} wants to buy {{ trigger.event.data.item_name }} for {{ trigger.event.data.item_cost }} in {{ trigger.event.data.league }}. Located in tab {{ trigger.event.data.tab_name }} at position left {{ trigger.event.data.left }}, top {{ trigger.event.data.top }}
        {% else %}
          PoE trade automation was run manually from within HA
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

## Usage

Run the script with:
```bash
python -u ha_poe_trade_notification.py
```
(-u runs the script without stdout buffering, otherwise you may not see stdout output right away)

The script will:
1. Monitor your PoE log file for trade requests
2. Parse out details like item name, price, and buyer
3. Send this data to Home Assistant
4. Trigger any automations you've set up (like flashing lights)

## Available Event Data

When a trade message comes in, these fields are available in Home Assistant automations under `trigger.event.data`:

- `date`: Date of trade request
- `time`: Time of trade request
- `buyer_name`: Name of the player wanting to buy
- `item_name`: The item they want to buy
- `item_cost`: Listed price
- `league`: Which league (Standard, etc)
- `tab_name`: Stash tab name
- `left`: Left position in stash tab
- `top`: Top position in stash tab

You can use these in your automations for custom notifications or other actions.