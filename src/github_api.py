import os
import requests
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = "https://api.github.com"

class GitHubAPI:
    def __init__(self, token):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _handle_response(self, response):
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
            reset_time = int(response.headers['X-RateLimit-Reset'])
            wait_time = max(0, reset_time - time.time())
            logging.warning(f"Rate limit reached. Waiting for {wait_time} seconds.")
            time.sleep(wait_time)
            return True
        response.raise_for_status()
        return False

    def _paginate(self, url, key=None):
        results = []
        while url:
            response = requests.get(url, headers=self.headers)
            if self._handle_response(response):
                continue
            data = response.json()
            if key:
                results.extend(data.get(key, []))
            else:
                results.extend(data)
            url = response.links.get('next', {}).get('url')
        return results

    def get_repositories(self):
        url = f"{GITHUB_API_URL}/user/repos"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        return self._paginate(url)

    def get_workflows(self, repo_full_name, filter_names=None, filter_paths=None, since=None):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        workflows = response.json().get('workflows', [])
        
        if filter_names:
            workflows = [wf for wf in workflows if wf['name'] in filter_names]
        if filter_paths:
            workflows = [wf for wf in workflows if wf['path'] in filter_paths]
        
        if workflows:
            logging.info(f"Workflows for {repo_full_name}:")
            for wf in workflows:
                logging.info(f"  - {wf['name']} (URL: {wf['url']})")
        else:
            logging.info(f"No workflows found for {repo_full_name}.")
        
        return workflows

    def get_workflow_runs(self, repo_full_name, workflow_id, since=None):
        """
        Fetches workflow runs for a given workflow in a repository, optionally filtering by creation date,
        and only including runs that are completed and have a conclusion of success or action_required.
        
        :param repo_full_name: Full repository name (e.g., "docker/cli").
        :param workflow_id: The ID of the workflow.
        :param since: A datetime object. Only workflow runs created on or after this date will be returned.
        :return: List of workflow runs.
        """
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/workflows/{workflow_id}/runs"
        params = {
            "status": "completed"  # Only return workflow runs with a status of completed.
        }
        if since:
            # Using the GitHub API's created query parameter to only return runs created after the given date.
            params['created'] = f">{since.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        
        response = requests.get(url, headers=self.headers, params=params)
        self._handle_response(response)
        workflow_runs = response.json().get('workflow_runs', [])
        
        # Ensure that the returned runs are created on or after the since date:
        if since:
            workflow_runs = [
                run for run in workflow_runs
                if datetime.strptime(run['created_at'], '%Y-%m-%dT%H:%M:%SZ') >= since
            ]
        
        # Filter to only include runs with conclusion either 'success' or 'action_required'
        allowed_conclusions = {"success", "action_required"}
        filtered_runs = [
            run for run in workflow_runs
            if run.get('conclusion') in allowed_conclusions
        ]
        
        return filtered_runs
    
    def get_jobs(self, repo_full_name, run_id):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            logging.warning(f"{Fore.YELLOW}⚠️ Job not found for run {run_id} in {repo_full_name}. Logs may have expired.{Style.RESET_ALL}")
            return []
        self._handle_response(response)
        return self._paginate(url, key='jobs')

    def search_files(self, repo_full_name, query):
        url = f"{GITHUB_API_URL}/search/code?q={query}+repo:{repo_full_name}"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        return response.json().get('items', [])

    def get_file_content(self, repo_full_name, path):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        content = response.json().get('content', '')
        return base64.b64decode(content).decode('utf-8')
