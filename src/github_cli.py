import os
import logging
import json
import click
from collections import defaultdict
from dotenv import load_dotenv
from github_api import GitHubAPI
from datetime import datetime

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
    logging.info(f"✅ Total repositories fetched: {len(repos)}")
    return repos

def group_repositories_by_namespace(repos, namespaces):
    """
    Groups repositories by their namespace (organization/user).

    :param repos: List of repositories.
    :param namespaces: List of selected namespaces to filter.
    :return: Dictionary of repositories grouped by namespace.
    """
    namespace_repos = defaultdict(list)

    for repo in repos:
        namespace = repo['full_name'].split('/')[0]  # Extract namespace
        if namespace in namespaces:
            namespace_repos[namespace].append(repo)
            logging.info(f"✅ Added repo to namespace {namespace}: {repo['full_name']}")

    return namespace_repos

def select_namespaces(repos):
    """
    Prompts the user to select which namespaces (organizations/users) to include.

    :param repos: List of repositories.
    :return: List of selected namespaces.
    """
    available_namespaces = set(repo['full_name'].split('/')[0] for repo in repos)
    
    logging.info(f"Available namespaces: {', '.join(available_namespaces)}")

    selected_namespaces = []
    for namespace in sorted(available_namespaces):
        if click.confirm(f"Assess repositories in {namespace}?", default=False):
            selected_namespaces.append(namespace)

    logging.info(f"✅ Selected namespaces: {', '.join(selected_namespaces)}")
    
    return selected_namespaces

def process_workflow_runs(github_api, repo_full_name, workflow):
    """
    Fetches workflow runs for a given workflow in a repository.

    :param github_api: Instance of GitHubAPI.
    :param repo_full_name: Full repository name (e.g., "org/repo").
    :param workflow: Dictionary containing workflow metadata.
    :return: List of workflow runs.
    """
    workflow_id = workflow.get('id')
    if not workflow_id:
        logging.warning(f"⚠️ Workflow {workflow.get('name', 'Unknown')} has no ID. Skipping.")
        return []

    workflow_runs = github_api.get_workflow_runs(repo_full_name, workflow_id)
    if not workflow_runs:
        logging.info(f"ℹ️ No workflow runs found for {workflow['name']} in {repo_full_name}.")
        return []

    logging.info(f"✅ Found {len(workflow_runs)} workflow runs for {workflow['name']} in {repo_full_name}.")
    return workflow_runs

def process_jobs(github_api, repo_full_name, run_id):
    """
    Fetches jobs for a given workflow run.

    :param github_api: Instance of GitHubAPI.
    :param repo_full_name: Full repository name (e.g., "org/repo").
    :param run_id: ID of the workflow run.
    :return: List of jobs.
    """
    jobs = github_api.get_jobs(repo_full_name, run_id)
    
    if not jobs:
        logging.info(f"ℹ️ No jobs found in workflow run {run_id} for {repo_full_name}.")
        return []

    logging.info(f"✅ Found {len(jobs)} jobs in workflow run {run_id} for {repo_full_name}.")
    return jobs




@click.command()
@click.option('--unique-steps', is_flag=True, help="Print unique step names to JSON")
@click.option('--force-continue', is_flag=True, help="Force continue even if there's an error")
@click.option('--filter-duration', type=int, default=0, help="Filter steps longer than the specified duration")
@click.option("--monthly-summary", is_flag=True, help="Generate monthly summary including all steps")
@click.option("--step-names-file", type=click.Path(), default=None, required=False, help="Either Path to JSON file containing step names or just straight flag to calculate totals")
def main(unique_steps, force_continue, filter_duration, monthly_summary, step_names_file):
    """ Main function to process GitHub workflow jobs with optional step name filtering. """
    
    github_api = GitHubAPI()
    output_data = []
    step_name_totals = defaultdict(float)

    # ✅ Load step names if provided
    step_names = load_step_names(step_names_file) if step_names_file else []

    # ✅ Fetch repositories
    repos = fetch_repositories(github_api)
    namespace_repos = group_repositories_by_namespace(repos, select_namespaces(repos))

    try:
        for namespace, repos in namespace_repos.items():
            logging.info(f"Processing namespace '{namespace}' with {len(repos)} repositories")
            for repo in repos:
                repo_full_name = repo['full_name']
                logging.info(f"Processing repository: {repo_full_name}")

                try:
                    workflows = github_api.get_workflows(repo_full_name)
                    for workflow in workflows:
                        logging.info(f"Workflow: {workflow['name']} (URL: {workflow['url']})")
                        workflow_runs = process_workflow_runs(github_api, repo_full_name, workflow)

                        for run in workflow_runs:
                            run_id = run['id']
                            try:
                                jobs = process_jobs(github_api, repo_full_name, run_id)
                                for job in jobs:
                                    logging.info(f"Processing job: {job['url']}")
                                    if not job.get('steps'):
                                        logging.warning(f"No steps found for job {job['id']}. Logs may have expired.")
                                        continue

                                    job['repo_full_name'] = repo_full_name
                                    job['workflow_name'] = workflow['name']
                                    job['run_id'] = run_id

                                    steps_data = process_steps(job, step_names, step_name_totals)
                                    output_data.extend(steps_data)

                            except Exception as e:
                                handle_error(f"Error fetching jobs for run {run_id} in {repo_full_name}: {e}", force_continue)

                except Exception as e:
                    handle_error(f"Error fetching workflows for repo {repo_full_name}: {e}", force_continue)

    except Exception as e:
        handle_error(f"General processing error: {e}", force_continue)

    # ✅ Save JSON Output
    save_output_json(output_data, step_name_totals, unique_steps, filter_duration, step_names_file, monthly_summary)

def process_steps(job, step_names, step_name_totals):
    """ Processes job steps, extracts metadata, and computes durations. """
    output_data = []
    for step in job['steps']:
        step_name = step['name']
        duration = calculate_duration(step.get('started_at'), step.get('completed_at'))

        step_data = {
            "step_name": step_name,
            "repo_full_name": job['repo_full_name'],
            "workflow_name": job['workflow_name'],
            "run_id": job['run_id'],
            "job_id": job['id'],
            "duration_seconds": duration,
            "started_at": step.get('started_at'),
            "completed_at": step.get('completed_at'),
            "url": job['url'],
            "html_url": job['html_url']
        }
        output_data.append(step_data)
        step_name_totals[step_name] += duration

    return output_data

def calculate_duration(start, end):
    """ Calculates duration between two timestamps. """
    if start and end:
        start_time = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
        end_time = datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')
        return (end_time - start_time).total_seconds()
    return None

def save_output_json(output_data, step_name_totals, unique_steps, filter_duration, step_names_file, monthly_summary):
    """ Saves filtered and aggregated JSON data to output files. """
    print(f'🔹 Unique steps flag: {unique_steps}')
    print(f'🔹 Total output data count: {len(output_data)}')

    # ✅ Extract unique step names only if `unique_steps` is True
    if unique_steps:
        filter_output = list({step['step_name']: step for step in output_data if 'step_name' in step}.values())
        unique_steps_data = sorted({step["step_name"] for step in filter_output if "step_name" in step})
        print(f'🔹 Unique steps extracted: {len(unique_steps_data)}')
        print(f'🔹 Sample data: {unique_steps_data[:5]}')  # ✅ Print first few entries

        # ✅ Only save if data exists
        if unique_steps_data:
            with open('step_names.json', 'w') as f:
                json.dump(unique_steps_data, f, indent=4)
            print("✅ step_names.json successfully saved!")
        else:
            print("⚠️ Warning: No unique steps found!")


    if filter_duration > 0:
        output_data = [step for step in output_data if step['duration_seconds'] and step['duration_seconds'] > filter_duration]

    if step_names_file:
        output_data = [step for step in output_data if step['step_name'] in step_name_totals]

    with open('stage_durations.json', 'w') as f:
        json.dump(output_data, f, indent=4)

    if monthly_summary:
        monthly_summary_data = get_monthly_stage_summary(output_data)
        with open('monthly_summary.json', 'w') as f:
            json.dump(monthly_summary_data, f, indent=4)

        logging.info("✅ Monthly summary saved.")

def get_monthly_stage_summary(data):
    """ Aggregates step durations per month. """
    monthly_summary = defaultdict(lambda: defaultdict(float))

    for step in data:
        start_time = step.get('started_at')
        if not start_time:
            continue

        month_key = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m')
        step_name = step['step_name']
        duration = step['duration_seconds'] or 0

        monthly_summary[month_key][step_name] += duration

    return {month: dict(steps) for month, steps in monthly_summary.items()}

def load_step_names(step_names_file):
    """ Loads step names from a JSON file. """
    if not step_names_file:
        return []

    if os.path.exists(step_names_file):
        try:
            with open(step_names_file, "r") as f:
                step_names = json.load(f)
            logging.info(f"✅ Loaded step names from {step_names_file}")
            return step_names
        except json.JSONDecodeError:
            logging.error(f"❌ Invalid JSON format in {step_names_file}. Exiting.")
            return []
    else:
        logging.error(f"❌ File {step_names_file} does not exist. Exiting.")
        return []

def handle_error(message, force_continue):
    """ Logs errors and determines whether to continue execution. """
    logging.error(message)
    if not force_continue:
        raise SystemExit("Exiting due to error.")
    logging.warning("Continuing execution...")

if __name__ == "__main__":
    main()
