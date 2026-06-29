import requests
import sys
import logging
import json
import os

logger = logging.getLogger(__name__)
# Route debug logs to stderr
handler = logging.StreamHandler(sys.stderr)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def fetch_recent_commits(repo: str, branch: str = 'main', limit: int = 30):
    """
    Fetch recent commits from a GitHub repository.
    
    :param repo: The repository in "owner/repo" format.
    :param branch: The branch to fetch commits from.
    :param limit: The maximum number of commits to return.
    :return: A list of dictionaries containing commit information.
    """
    logger.debug(f"Fetching up to {limit} commits for {repo} on branch {branch}")
    
    base_url = f"https://api.github.com/repos/{repo}/commits"
    params = {
        'sha': branch,
        'per_page': limit
    }
    
    headers = {}
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f"Bearer {github_token}"
        
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        commits = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch commits: {e}")
        return []

    result = []
    
    for c in commits:
        sha = c.get('sha')
        commit_data = c.get('commit', {})
        message = commit_data.get('message', '')
        author_name = commit_data.get('author', {}).get('name', '')
        
        # We need to fetch individual commit to get the files modified
        logger.debug(f"Fetching details for commit {sha}")
        try:
            commit_detail_response = requests.get(f"{base_url}/{sha}", headers=headers)
            commit_detail_response.raise_for_status()
            commit_detail = commit_detail_response.json()
            
            modified_files = [file.get('filename') for file in commit_detail.get('files', [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch details for commit {sha}: {e}")
            modified_files = []
            
        result.append({
            'message': message,
            'author_name': author_name,
            'modified_files': modified_files
        })
        
    return result
