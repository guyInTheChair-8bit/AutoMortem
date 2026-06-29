import os
import sys
import logging
from google import genai

# Configure logging to stderr
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

def generate_postmortem(task2_output: str, task3_output: str, api_key: str = None) -> str:
    """
    Synthesizes outputs from Task 2 and Task 3 into a strict Markdown postmortem.
    
    Args:
        task2_output: The outputs from metric/log analysis.
        task3_output: The outputs from code/config changes analysis.
        api_key: Optional API key for Google GenAI. If not provided, it will try to use the environment variable.
        
    Returns:
        A markdown formatted string containing the postmortem.
    """
    logger.debug("Initializing Google GenAI client.")
    
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = genai.Client()
        
    prompt = f"""
You are a Senior Site Reliability Engineer (SRE). Your task is to write a postmortem based on the provided Slack chat logs and GitHub commit history.
You must output in strict Markdown format.
You must include the following sections exactly:
1. Chronological Timeline
2. Root Cause
3. Action Items

CRITICAL RULES:
- Do NOT hallucinate or invent any server names, IP addresses, or metrics that are not present in the provided inputs.
- You must carefully analyze BOTH the Slack logs and the GitHub commits to figure out how they correlate. Identify which PR or commit caused the issue mentioned in the chat.
- Only use the facts provided below.
- Keep the tone professional and blameless.

Inputs from Task 2 (Slack Chat Logs):
{task2_output}

Inputs from Task 3 (GitHub Commits):
{task3_output}
"""
    
    logger.debug("Sending prompt to LLM.")
    try:
        # Using gemini-2.5-pro as a default capable model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        logger.debug("Received response from LLM.")
        return response.text
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        raise
