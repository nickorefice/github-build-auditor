import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import click
from github_api import GitHubAPI
from dotenv import load_dotenv
import json
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("project.log")
    ]
)

def fetch_repositories(github_api):
    repos = github_api.get_repositories()
    logging.info(f"Total repositories fetched: {len(repos)}")
    return repos

def group_repositories_by_namespace(repos, namespaces):
    namespace_repos = defaultdict(list)
    for repo in repos:
        namespace = repo['full_name'].split('/')[0]
        if namespace in namespaces:
            namespace_repos[namespace].append(repo)
            logging.info(f"  - {repo['full_name']}")
    return namespace_repos

def process_workflow_runs(github_api, repo_full_name, workflow):
    workflow_id = workflow['id']
    workflow_runs = github_api.get_workflow_runs(repo_full_name, workflow_id)
    if not workflow_runs:
        logging.info(f"No workflow runs found for workflow {workflow['name']}")
        return []
    logging.info(f"Found {len(workflow_runs)} workflow runs for workflow {workflow['name']}")
    return workflow_runs

def process_jobs(github_api, repo_full_name, run_id):
    jobs = github_api.get_jobs(repo_full_name, run_id)
    if not jobs:
        logging.info(f"No jobs found in workflow run {run_id}")
        return []
    logging.info(f"Found {len(jobs)} jobs in workflow run {run_id}")
    return jobs

def process_steps(job, step_names, step_name_totals):
    output_data = []
    total_actions_assessed = 0
    for step in job['steps']:
        total_actions_assessed += 1
        step_name = step['name']
        step_number = step['number']
        step_started_at = step.get('started_at')
        step_completed_at = step.get('completed_at')
        step_status = step.get('status')
        step_conclusion = step.get('conclusion')  
        step_url = job['url']
        step_html_url = job['html_url']
        duration = None
        if step_started_at and step_completed_at:
            start_time = datetime.strptime(step_started_at, '%Y-%m-%dT%H:%M:%SZ')
            end_time = datetime.strptime(step_completed_at, '%Y-%m-%dT%H:%M:%SZ')
            duration = (end_time - start_time).total_seconds()
            month_key = start_time.strftime('%Y-%m')
            if step_name in step_names:
                step_name_totals[month_key][step_name]['duration'] += duration
                step_name_totals[month_key][step_name]['count'] += 1
        step_data = {
            "step_name": step_name,
            "repo_full_name": job['repo_full_name'],
            "workflow_name": job['workflow_name'],
            "run_id": job['run_id'],
            "job_id": job['id'],
            "step_number": step_number,
            "started_at": step_started_at,
            "completed_at": step_completed_at,
            "duration_seconds": duration,
            "status": step_status,
            "conclusion": step_conclusion,
            "url": step_url,
            "html_url": step_html_url
        }
        output_data.append(step_data)
    return output_data, total_actions_assessed

@click.command()
@click.option('--unique-steps', is_flag=True, help="Print unique step names to JSON")
@click.option('--force-continue', is_flag=True, help="Force continue even if there's an error without prompting the user")
@click.option('--filter-duration', type=int, default=0, help="Filter for steps with duration longer than the specified value in seconds")
@click.option('--step-names-file', type=click.Path(exists=True), help="Path to JSON file containing step names to calculate totals")
def main(unique_steps, force_continue, filter_duration, step_names_file):
    username = os.getenv('GITHUB_USERNAME')
    if not username:
        raise ValueError("GitHub username must be set in the .env file")

    github_api = GitHubAPI()
    output_data = []
    total_repositories_assessed = 0
    total_actions_assessed = 0
    total_jobs_assessed = 0
    total_empty_jobs = 0
    success = True

    step_name_totals = defaultdict(lambda: defaultdict(lambda: {'duration': 0.0, 'count': 0}))

    if step_names_file:
        with open(step_names_file, 'r') as f:
            step_names = json.load(f)
    else:
        step_names = []

    # Fetch repositories and determine available namespaces
    repos = fetch_repositories(github_api)
    available_namespaces = set(repo['full_name'].split('/')[0] for repo in repos)

    # Prompt user for namespaces
    namespaces = []
    for namespace in available_namespaces:
        if click.confirm(f"Assess repositories in {namespace}", default=False):
            namespaces.append(namespace)

    namespace_repos = group_repositories_by_namespace(repos, namespaces)

    try:
        for namespace, repos in namespace_repos.items():
            print(f"\n{Fore.GREEN}Namespace '{namespace}' has {len(repos)} repositories:{Style.RESET_ALL}")
            for repo in repos:
                repo_full_name = repo['full_name']
                total_repositories_assessed += 1
                print(f"  {Fore.CYAN}- {repo_full_name}{Style.RESET_ALL}")
                try:
                    workflows = github_api.get_workflows(repo_full_name)
                    if not workflows:
                        print(f"    {Fore.RED}No workflows found in {repo_full_name}{Style.RESET_ALL}")
                        continue
                    print(f"    {Fore.GREEN}Found {len(workflows)} workflows in {repo_full_name}{Style.RESET_ALL}")
                    for workflow in workflows:
                        print(f"      {Fore.YELLOW}Workflow: {workflow['name']} (URL: {workflow['url']}){Style.RESET_ALL}")
                        try:
                            workflow_runs = process_workflow_runs(github_api, repo_full_name, workflow)
                            for run in workflow_runs:
                                run_id = run['id']
                                try:
                                    jobs = process_jobs(github_api, repo_full_name, run_id)
                                    total_jobs_assessed += len(jobs)
                                    print(f"        {Fore.MAGENTA}Workflow run: {run_id}{Style.RESET_ALL}")
                                    for job in jobs:
                                        print(f"          {Fore.BLUE}Job URL: {job['url']}{Style.RESET_ALL}")
                                        if not job.get('steps'):
                                            print(f"          {Fore.RED}Steps are empty for job {job['id']} in workflow run {run_id}. Logs may have expired.{Style.RESET_ALL}")
                                            total_empty_jobs += 1
                                            continue
                                        print(f"          {Fore.GREEN}Found {len(job['steps'])} steps in job {job['id']} in workflow run {run_id}{Style.RESET_ALL}")
                                        for step in job['steps']:
                                            print(f"            {Fore.YELLOW}Step: {step['name']}{Style.RESET_ALL}")
                                        job['repo_full_name'] = repo_full_name
                                        job['workflow_name'] = workflow['name']
                                        job['run_id'] = run_id
                                        steps_data, actions_assessed = process_steps(job, step_names, step_name_totals)
                                        output_data.extend(steps_data)
                                        total_actions_assessed += actions_assessed
                                except Exception as e:
                                    logging.error(f"Error fetching jobs for run {run_id} in workflow {workflow['name']} of repo {repo_full_name}: {e}")
                                    if not force_continue:
                                        if click.confirm('An error occurred. Do you want to continue?', default=False):
                                            continue
                                        else:
                                            success = False
                                            break
                        except Exception as e:
                            logging.error(f"Error fetching workflow runs for workflow {workflow['name']} in repo {repo_full_name}: {e}")
                            if not force_continue:
                                if click.confirm('An error occurred. Do you want to continue?', default=False):
                                    continue
                                else:
                                    success = False
                                    break
                except Exception as e:
                    logging.error(f"Error fetching workflows for repo {repo_full_name}: {e}")
                    if not force_continue:
                        if click.confirm('An error occurred. Do you want to continue?', default=False):
                            continue
                        else:
                            success = False
                            break
    except Exception as e:
        logging.error(f"Error: {e}")
        success = False

    # Write output data to a JSON file
    if success:
        if unique_steps:
            unique_steps_data = []
            seen_steps = set()
            for step in output_data:
                if step['step_name'] not in seen_steps:
                    unique_steps_data.append(step)
                    seen_steps.add(step['step_name'])
            output_data = unique_steps_data

        # Filter steps by minimum duration
        if filter_duration > 0:
            output_data = [step for step in output_data if step['duration_seconds'] > filter_duration]

        # Filter steps by step names if step_names_file is provided
        if step_names_file:
            output_data = [step for step in output_data if step['step_name'] in step_names]

        with open('steps_output.json', 'w') as f:
            json.dump(output_data, f, indent=4)

        # Log and write totals for specified step names by month
        step_name_totals_by_month = defaultdict(lambda: defaultdict(lambda: {'duration': 0.0, 'count': 0}))
        for month_key, step_totals in step_name_totals.items():
            for step_name, totals in step_totals.items():
                step_name_totals_by_month[month_key][step_name] = {
                    'duration': totals['duration'],
                    'count': totals['count']
                }

        # Sort the step_name_totals_by_month by date in descending order
        sorted_step_name_totals_by_month = OrderedDict(sorted(step_name_totals_by_month.items(), reverse=True))

        with open('step_name_totals.json', 'w') as f:
            json.dump(sorted_step_name_totals_by_month, f, indent=4)

        print(f"\n{Fore.GREEN}Summary:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total repositories assessed: {Fore.YELLOW}{total_repositories_assessed}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total actions assessed: {Fore.YELLOW}{total_actions_assessed}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total jobs assessed: {Fore.YELLOW}{total_jobs_assessed}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total empty jobs (logs may have expired): {Fore.YELLOW}{total_empty_jobs}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Script execution failed. No summary information will be logged.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()