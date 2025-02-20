import os
import requests
import logging
from dotenv import load_dotenv
import base64
import time

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = "https://api.github.com"

class GitHubAPI:
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
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

    def _paginate(self, url, params=None, key=None):
        results = []
        while url:
            response = requests.get(url, headers=self.headers, params=params)
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

    def get_workflows(self, repo_full_name, filter_names=None, filter_paths=None):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        workflows = response.json().get('workflows', [])
        logging.info(f"Workflows response for {repo_full_name}: {[{'name': wf['name'], 'url': wf['url']} for wf in workflows]}")
        
        if filter_names:
            workflows = [wf for wf in workflows if wf['name'] in filter_names]
        if filter_paths:
            workflows = [wf for wf in workflows if wf['path'] in filter_paths]
        
        return workflows

    def get_workflow_runs(self, repo_full_name, workflow_id):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/workflows/{workflow_id}/runs"
        return self._paginate(url, key='workflow_runs')

    def get_jobs(self, repo_full_name, run_id):
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        self._handle_response(response)
        jobs = response.json().get('jobs', [])
        logging.info(f"Jobs response for run {run_id} in repo {repo_full_name}: {[job['url'] for job in jobs]}")
        return jobs

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
