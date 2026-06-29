import os
import sys
import time
import re
import logging
import requests
from typing import List, Dict, Any

# Configure logging to write to stderr
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def fetch_incident_logs(channel_id: str, minutes_back: int = 1440) -> List[Dict[str, Any]]:
    """
    Fetches incident logs from a Slack channel.
    Strips custom emojis, ignores system join/leave messages, and translates <@U12345> into User_U12345.
    """
    logger.info(f"Fetching incident logs for channel {channel_id}, going back {minutes_back} minutes")
    
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        logger.error("SLACK_BOT_TOKEN environment variable not set")
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")
    
    url = "https://slack.com/api/conversations.history"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # We fetch the latest 100 messages regardless of time
    # oldest calculation removed
    
    params = {
        "channel": channel_id
    }
    
    logger.debug(f"Making request to Slack API: {url} with params: channel={channel_id}")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        logger.error(f"Slack API request failed with status {response.status_code}: {response.text}")
        response.raise_for_status()
        
    data = response.json()
    
    if not data.get("ok"):
        error_msg = data.get("error", "Unknown error")
        logger.error(f"Slack API returned error: {error_msg}")
        raise ValueError(f"Slack API error: {error_msg}")
        
    messages = data.get("messages", [])
    logger.info(f"Retrieved {len(messages)} messages from Slack API")
    
    structured_logs = []
    
    # Regex for custom emojis: :emoji_name:
    emoji_pattern = re.compile(r':[a-zA-Z0-9_+-]+:')
    # Regex for user mentions: <@U12345>
    user_pattern = re.compile(r'<@(U[A-Z0-9]+)>')
    
    for msg in messages:
        # Ignore system join/leave messages
        subtype = msg.get("subtype")
        if subtype in ("channel_join", "channel_leave"):
            logger.debug(f"Skipping system message of subtype: {subtype}")
            continue
            
        text = msg.get("text", "")
        
        # Strip custom emojis
        text = emoji_pattern.sub('', text)
        
        # Translate <@U12345> into User_U12345
        text = user_pattern.sub(r'User_\1', text)
        
        # Clean up double spaces caused by emoji stripping
        text = ' '.join(text.split())
        
        structured_logs.append({
            "ts": msg.get("ts"),
            "user": msg.get("user"),
            "text": text,
            "type": msg.get("type"),
            "subtype": subtype
        })
        
    logger.info(f"Successfully processed {len(structured_logs)} valid incident logs")
    return structured_logs
