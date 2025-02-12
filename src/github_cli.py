import os
import logging
import json
import click
from collections import defaultdict
from dotenv import load_dotenv
from github_api import GitHubAPI
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("project.log"), logging.StreamHandler()],
)

def fetch_repositories(github_api):
    """ Fetch all repositories from GitHub API. """
    repos = github_api.get_repositories()
    logging.info(f"{Fore.GREEN}✅ Total repositories fetched: {len(repos)}{Style.RESET_ALL}")
    return repos

[rest of the file content...]