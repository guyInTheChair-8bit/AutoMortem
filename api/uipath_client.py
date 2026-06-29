import sys
import os
import logging
import requests
from dotenv import load_dotenv

# 1. Force Python to read the .env file in the current directory
load_dotenv()

# Configure logging to route all debug logs to stderr, not stdout
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

def push_to_uipath_queue(report_markdown: str, incident_id: str) -> None:
    """
    Push a postmortem report to the UiPath queue.
    """
    logger.debug(f"Starting push_to_uipath_queue for incident: {incident_id}")
    
    # 2. Grab the keys (No fallback strings so we fail fast if .env is missing)
    client_id = os.getenv("UIPATH_CLIENT_ID")
    client_secret = os.getenv("UIPATH_CLIENT_SECRET")
    
    # 3. Log exactly what we found (masking the secret for safety)
    logger.info(f"🔑 Auth Check - Client ID: {client_id}")
    if client_secret:
        logger.info("🔑 Auth Check - Client Secret is loaded (Hidden)")
    else:
        logger.error("❌ Auth Check - Client Secret is NONE!")
        
    # Safety catch
    if not client_id or not client_secret:
        raise ValueError("UiPath credentials are missing! Python cannot see the .env file.")
        
    # 4. Obtain OAuth 2.0 Bearer token
    oauth_url = "https://cloud.uipath.com/identity_/connect/token"
    
    oauth_payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "OR.Queues OR.Queues.Write"
    }
    
    logger.debug(f"Requesting Bearer token from {oauth_url}")
    try:
        token_response = requests.post(oauth_url, data=oauth_payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("Access token not found in the OAuth response.")
            raise ValueError("Failed to retrieve access token")
            
        logger.debug("Successfully retrieved Bearer token.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Error during OAuth token request: {e}")
        raise
        
    # 5. Push to UiPath Queue
    # Ensure UIPATH_BASE_URL is set in your .env (e.g., https://cloud.uipath.com/YOUR_ORG/YOUR_TENANT)
    base_url = os.getenv("UIPATH_BASE_URL")
    if not base_url:
        raise ValueError("UIPATH_BASE_URL is missing from .env file!")
        
    queue_url = f"{base_url.rstrip('/')}/orchestrator_/odata/Queues/UiPathODataSvc.AddQueueItem"
    
    folder_id = os.getenv("UIPATH_FOLDER_ID")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if folder_id:
        headers["X-UIPATH-OrganizationUnitId"] = str(folder_id)
        
    queue_payload = {
        "itemData": {
            "Name": "SRE_PostMortem_Approvals",
            "Priority": "Normal",
            "SpecificContent": {
                "IncidentID": incident_id,
                "ReportMarkdown": report_markdown
            },
            "Reference": incident_id
        }
    }
    
    logger.debug(f"Sending AddQueueItem POST request to {queue_url}")
    try:
        queue_response = requests.post(queue_url, json=queue_payload, headers=headers)
        queue_response.raise_for_status()
        logger.debug(f"Successfully added queue item SRE_PostMortem_Approvals for incident {incident_id}.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Error while pushing to UiPath queue: {e}")
        raise
