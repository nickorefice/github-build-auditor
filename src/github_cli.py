import os
import logging
import json
from collections import defaultdict, OrderedDict
import click
from dotenv import load_dotenv
from github_api import GitHubAPI
from colorama import init, Fore, Style
from datetime import datetime, timedelta, timezone

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Configure logging
file_handler = logging.FileHandler("project.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Set console handler to WARNING level
console_handler.setFormatter(logging.Formatter('%(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

def fetch_repositories(github_api, since=None):
    """ Fetch all repositories from GitHub API updated since the given date. """
    print(f"Searching for repositories...")
    repos = github_api.get_repositories(since)
    print(f"✅ Total repositories fetched: {len(repos)}")
    logging.info(f"✅ Total repositories fetched: {len(repos)}")
    return repos

def parse_repositories(repos):
    """ 
    Parse repositories to keep only full_name, html_url, description, and updated_at.
    Excludes repositories that are archived or disabled.
    Returns the filtered repositories sorted by updated_at (descending).
    """
    parsed_repos = []
    for repo in repos:
        # Exclude repositories that are archived or disabled
        if repo.get("archived") or repo.get("disabled"):
            continue
        parsed_repo = {
            "full_name": repo.get("full_name"),
            "html_url": repo.get("html_url"),
            "description": repo.get("description"),
            "updated_at": repo.get("updated_at"),
        }
        parsed_repos.append(parsed_repo)
    
    # Sort repositories by updated_at in descending order (latest first)
    sorted_repos = sorted(parsed_repos, key=lambda r: r.get("updated_at", ""), reverse=True)
    return sorted_repos

def load_repositories_from_file(file_path):
    """ Load repositories from a JSON file. """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                repos = json.load(f)
            logging.info(f"✅ Loaded repositories from {file_path}")
            return repos
        except json.JSONDecodeError:
            logging.error(f"❌ Invalid JSON format in {file_path}. Exiting.")
            return []
    else:
        logging.error(f"❌ File {file_path} does not exist. Exiting.")
        return []

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

def process_workflow_runs(github_api, repo_full_name, workflow, since=None):
    """
    Fetches workflow runs for a given workflow in a repository and prints feedback to the terminal.
    
    :param github_api: Instance of GitHubAPI.
    :param repo_full_name: Full repository name (e.g., "docker/pinata").
    :param workflow: Dictionary containing workflow metadata.
    :param since: Datetime object. Only workflow runs created on or after this date will be returned.
    :return: List of workflow runs.
    """
    workflow_id = workflow.get('id')
    if not workflow_id:
        logging.warning(f"⚠️ Workflow {workflow.get('name', 'Unknown')} has no ID. Skipping.")
        return []
    
    # Provide formatted feedback to the user
    print(f"{Fore.CYAN}  Assessing workflow: '{workflow.get('name', 'Unknown')}' (ID: {workflow_id})...{Style.RESET_ALL}")
    
    workflow_runs = github_api.get_workflow_runs(repo_full_name, workflow_id, since)
    
    # Print count feedback to terminal in a formatted manner
    print(f"{Fore.GREEN}  Found {len(workflow_runs)} workflow run{'s' if len(workflow_runs) != 1 else ''} for '{workflow.get('name', 'Unknown')}'{Style.RESET_ALL}")
    logging.info(f"✅ Found {len(workflow_runs)} workflow runs for {workflow.get('name', 'Unknown')} in {repo_full_name}.")
    
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
@click.option('--skip-labels', multiple=True, help="Labels of jobs to skip")
@click.option('--filter-names', multiple=True, help="Names of workflows to include")
@click.option('--filter-paths', multiple=True, help="Paths of workflows to include")
@click.option('--since', type=click.DateTime(formats=["%Y-%m-%d"]), help="Fetch workflow runs since this date (YYYY-MM-DD)")
@click.option('--dump-repos', is_flag=True, help="Dump all repositories to a JSON file")
@click.option('--repos-file', type=click.Path(), default=None, help="Path to JSON file containing repositories to process")
def main(unique_steps, force_continue, filter_duration, monthly_summary, step_names_file, skip_labels, filter_names, filter_paths, since, dump_repos, repos_file):
    """ Main function to process GitHub workflow jobs with optional step name filtering. """
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GitHub token must be set in the environment variables")

    github_api = GitHubAPI(token)

    # Dump repositories if --dump-repos is provided
    if dump_repos:
        since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        repos = fetch_repositories(github_api, since=since_date)
        # Prompt the user to select namespaces from the fetched repositories
        selected_namespaces = select_namespaces(repos)
        # Filter repositories by selected namespaces
        filtered_repos = [repo for repo in repos if repo.get("full_name", "").split('/')[0] in selected_namespaces]
        parsed_repos = parse_repositories(filtered_repos)
        with open('repositories.json', 'w') as f:
            json.dump(parsed_repos, f, indent=4)
        logging.info("✅ Repositories dumped to repositories.json")
        return

    # Load repositories from file if --repos-file is provided
    if repos_file:
        repos = load_repositories_from_file(repos_file)
    else:
        repos = fetch_repositories(github_api)

    output_data = []
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

    namespace_repos = group_repositories_by_namespace(repos, select_namespaces(repos))

    try:
        for namespace, repos in namespace_repos.items():
            logging.info(f"Processing namespace '{namespace}' with {len(repos)} repositories")
            for repo in repos:
                repo_full_name = repo['full_name']
                logging.info(f"Processing repository: {repo_full_name}")

                try:
                    workflows = github_api.get_workflows(repo_full_name, filter_names, filter_paths, since)
                    # Print out total active workflows for the repository
                    print(f"{Style.BRIGHT}Repository: {repo_full_name} - Active workflows count: {len(workflows)}{Style.RESET_ALL}")
                    
                    for workflow in workflows:
                        logging.info(f"Workflow: {workflow['name']} (URL: {workflow['url']})")
                        workflow_runs = process_workflow_runs(github_api, repo_full_name, workflow, since)

                        for run in workflow_runs:
                            run_id = run['id']
                            try:
                                jobs = process_jobs(github_api, repo_full_name, run_id)
                                filtered_jobs = filter_jobs(jobs, skip_labels)
                                total_jobs_assessed += len(filtered_jobs)
                                for job in filtered_jobs:
                                    logging.info(f"Processing job: {job['url']}")
                                    if not job.get('steps'):
                                        logging.info(f"No steps found for job {job['id']}. Logs may have expired.")
                                        total_empty_jobs += 1
                                        continue

                                    job['repo_full_name'] = repo_full_name
                                    job['workflow_name'] = workflow['name']
                                    job['run_id'] = run_id

                                    steps_data, actions_assessed = process_steps(job, step_names, step_name_totals)
                                    output_data.extend(steps_data)
                                    total_actions_assessed += actions_assessed

                            except Exception as e:
                                handle_error(f"Error fetching jobs for run {run_id} in {repo_full_name}: {e}", force_continue)

                except Exception as e:
                    handle_error(f"Error fetching workflows for repo {repo_full_name}: {e}", force_continue)

    except Exception as e:
        handle_error(f"General processing error: {e}", force_continue)

    # Save JSON Output
    save_output_json(output_data, step_name_totals, unique_steps, filter_duration, step_names_file, monthly_summary)

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
        print(f"Total actions assessed: {total_actions_assessed}")
        print(f"Total jobs assessed: {total_jobs_assessed}")
        print(f"Total empty jobs (logs may have expired): {total_empty_jobs}")
    else:
        print(f"{Fore.RED}Script execution failed. No summary information will be logged.{Style.RESET_ALL}")

def process_steps(job, step_names, step_name_totals):
    """ Processes job steps, extracts metadata, and computes durations. """
    output_data = []
    total_actions_assessed = 0
    for step in job['steps']:
        total_actions_assessed += 1
        step_name = step['name']
        step_started_at = step.get('started_at')
        step_completed_at = step.get('completed_at')
        step_status = step.get('status')
        step_conclusion = step.get('conclusion')
        step_url = job['url']
        step_html_url = job['html_url']
        duration = calculate_duration(step_started_at, step_completed_at)
        step_data = {
            "step_name": step_name,
            "repo_full_name": job['repo_full_name'],
            "workflow_name": job['workflow_name'],
            "run_id": job['run_id'],
            "job_id": job['id'],
            "duration_seconds": duration,
            "started_at": step_started_at,
            "completed_at": step_completed_at,
            "status": step_status,
            "conclusion": step_conclusion,
            "url": step_url,
            "html_url": step_html_url
        }
        output_data.append(step_data)
    return output_data, total_actions_assessed

def calculate_duration(started_at, completed_at):
    if started_at and completed_at and started_at != 'null' and completed_at != 'null':
        try:
            start_time = datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%SZ')
            end_time = datetime.strptime(completed_at, '%Y-%m-%dT%H:%M:%SZ')
            return (end_time - start_time).total_seconds()
        except ValueError as e:
            logging.error(f"Error parsing dates: {e}")
            return None
    return None

def save_output_json(output_data, step_name_totals, unique_steps, filter_duration, step_names_file, monthly_summary):
    """ Saves filtered and aggregated JSON data to output files. """
    print(f'🔹 Unique steps flag: {unique_steps}')
    print(f'🔹 Total output data count: {len(output_data)}')

    # Extract unique step names only if `unique_steps` is True
    if unique_steps:
        filter_output = list({step['step_name']: step for step in output_data if 'step_name' in step}.values())
        unique_steps_data = sorted({step["step_name"] for step in filter_output if "step_name" in step})
        print(f'🔹 Unique steps extracted: {len(unique_steps_data)}')
        print(f'🔹 Some steps found include: {unique_steps_data[:5]}')

        # Only save if data exists
        if unique_steps_data:
            with open('step_names.json', 'w') as f:
                json.dump(unique_steps_data, f, indent=4)
            print(f"✅ step_names.json successfully saved!")
        else:
            print(f"⚠️ Warning: No unique steps found!")

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
    """ 
    Aggregates step durations and counts per month.
    Converts total step duration from seconds to minutes.
    Returns a dictionary with each month as key and an ordered dictionary for each step (sorted by duration_minutes in descending order).
    """
    from collections import defaultdict, OrderedDict
    # Aggregate durations (in seconds) and counts per step name in each month:
    monthly_summary = defaultdict(lambda: defaultdict(lambda: {"duration": 0.0, "count": 0}))
    
    for step in data:
        start_time = step.get('started_at')
        if not start_time:
            continue
        # Group by month key using the started_at timestamp
        month_key = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m')
        step_name = step['step_name']
        duration = step.get('duration_seconds') or 0
        monthly_summary[month_key][step_name]["duration"] += duration
        monthly_summary[month_key][step_name]["count"] += 1

    # For each month convert duration to minutes and sort the steps by duration_minutes (descending)
    monthly_summary_in_minutes = {}
    for month, steps in monthly_summary.items():
        # Convert seconds to minutes for each step
        steps_with_minutes = {
            name: {
                "duration_minutes": metrics["duration"] / 60.0,
                "count": metrics["count"]
            } for name, metrics in steps.items()
        }
        # Sort the steps by duration_minutes in descending order:
        sorted_steps = OrderedDict(
            sorted(steps_with_minutes.items(), key=lambda item: item[1]["duration_minutes"], reverse=True)
        )
        monthly_summary_in_minutes[month] = sorted_steps

    return monthly_summary_in_minutes

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

def filter_jobs(jobs, skip_labels):
    filtered_jobs = []
    for job in jobs:
        job_labels = job.get('labels', [])
        if any(label in skip_labels for label in job_labels):
            logging.info(f"Skipping job {job['id']} due to label match: {job_labels}")
            continue
        filtered_jobs.append(job)
    logging.info(f"Found {len(filtered_jobs)} jobs after filtering")
    return filtered_jobs

if __name__ == "__main__":
    main()