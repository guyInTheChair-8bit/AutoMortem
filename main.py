import argparse
import sys
import json
import logging
import os
from dotenv import load_dotenv

from api.slack_client import fetch_incident_logs
from api.github_client import fetch_recent_commits
from core.synthesizer import generate_postmortem
from markdown_pdf import Section, MarkdownPdf

# Set up logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Fetch, synthesize, and push to UiPath.")
    parser.add_argument("--channel_id", required=True, help="Slack channel ID")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    
    args = parser.parse_args()
    
    load_dotenv()
    
    try:
        logger.info(f"Starting process for channel_id: {args.channel_id} and repo: {args.repo}")
        
        # Call fetchers
        logger.info("Calling fetchers...")
        slack_data = fetch_incident_logs(channel_id=args.channel_id)
        github_data = fetch_recent_commits(repo=args.repo)
        
        # Call synthesizer
        logger.info("Calling synthesizer...")
        slack_json = json.dumps(slack_data)
        github_json = json.dumps(github_data)
        summary = generate_postmortem(task2_output=slack_json, task3_output=github_json)
        
        # Save locally as a PDF
        logger.info("Saving report as PDF...")
        incident_id = f"INC-{args.channel_id}"
        
        # Prepend an H1 header to ensure the TOC hierarchy is valid, and disable TOC generation
        pdf = MarkdownPdf(toc_level=0)
        safe_summary = f"# Incident Postmortem: {incident_id}\n\n" + summary
        pdf.add_section(Section(safe_summary))
        pdf_filename = f"postmortem_{incident_id}.pdf"
        pdf.save(pdf_filename)
        
        # Final output to stdout must be flat JSON
        output = {
            "status": "success",
            "pdf_saved": pdf_filename
        }
        
        # Print JSON to stdout
        print(json.dumps(output))
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        error_output = {
            "status": "error",
            "message": str(e)
        }
        # Print JSON error to stdout
        print(json.dumps(error_output))
        sys.exit(1)

if __name__ == "__main__":
    main()
