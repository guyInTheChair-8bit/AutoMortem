from flask import Flask, jsonify, request
import subprocess
import logging
import sys

app = Flask(__name__)

# Route debug logs to stderr to keep stdout clean
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

@app.route('/generate-postmortem', methods=['POST'])
def generate_postmortem():
    logger.info("Received POST request from UiPath Maestro!")
    
    # Extract the Incident ID sent by Maestro
    data = request.json or {}
    incident_id = data.get("incidentId", "UNKNOWN_INCIDENT")
    
    # Hardcoded dummy variables for the hackathon demo (Slack channel & GitHub repo)
    channel_id = "C0BDYF2Q87N" 
    repo_name = "guyInTheChair-8bit/maestro-test"
    
    try:
        # Fire off the CLI script generated earlier
        logger.info(f"Triggering main.py for incident {incident_id}...")
        
        # The '-u' flag forces unbuffered output, making logs stream in real-time
        # stdout and stderr are routed to sys to print directly to the Flask terminal
        subprocess.Popen(
            ["python3", "-u", "main.py", "--channel_id", channel_id, "--repo", repo_name],
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        
        # Immediately return a 200 OK so UiPath knows the handoff was successful
        return jsonify({"status": "success", "message": f"Worker triggered for {incident_id}"}), 200
        
    except Exception as e:
        logger.error(f"Failed to trigger worker: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
