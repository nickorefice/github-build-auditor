import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import click
from github_api import GitHubAPI
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("project.log"),
        logging.StreamHandler()
    ]
)

@click.command()
@click.option('--unique-steps', is_flag=True, help="Print unique step names to JSON")
@click.option('--force-continue', is_flag=True, help="Force continue even if there's an error without prompting the user")
@click.option('--min-duration', type=int, default=0, help="Minimum duration in seconds to filter steps")
@click.option('--step-names-file', type=click.Path(exists=True), help="Path to JSON file containing step names to calculate totals")
def main(unique_steps, force_continue, min_duration, step_names_file):
    username = os.getenv('GITHUB_USERNAME')
    if not username:
        raise ValueError("GitHub username must be set in the .env file")

    github_api = GitHubAPI()
    total_duration_build_push = timedelta()
    total_duration_setup_qemu = timedelta()
    output_data = []
    total_repositories_assessed = 0
    total_actions_assessed = 0
    total_jobs_assessed = 0
    total_empty_jobs = 0
    success = True

    step_name_totals = defaultdict(float)

    if step_names_file:
        with open(step_names_file, 'r') as f:
            step_names = json.load(f)
    else:
        step_names = []

    try:
        repos = github_api.get_repositories()
        logging.info(f"Total repositories fetched: {len(repos)}")

        # Group repositories by namespace
        namespace_repos = defaultdict(list)
        for repo in repos:
            namespace = repo['full_name'].split('/')[0]
            if namespace == 'nickorefice':  # Filter by namespace 'nickorefice'
                namespace_repos[namespace].append(repo)
                logging.info(f"  - {repo['full_name']}")

        for namespace, repos in namespace_repos.items():
            logging.info(f"Namespace '{namespace}' has {len(repos)} repositories")
            for repo in repos:
                repo_full_name = repo['full_name']
                total_repositories_assessed += 1
                logging.info(f"Processing repository: {repo_full_name}")
                try:
                    workflows = github_api.get_workflows(repo_full_name)
                    if not workflows:
                        logging.info(f"No workflows found in {repo_full_name}")
                        continue
                    logging.info(f"Found {len(workflows)} workflows in {repo_full_name}")
                    for workflow in workflows:
                        logging.info(f"Workflow: {workflow['name']} (URL: {workflow['url']})")
                        workflow_id = workflow['id']
                        try:
                            workflow_runs = github_api.get_workflow_runs(repo_full_name, workflow_id)
                            if not workflow_runs:
                                logging.info(f"No workflow runs found for workflow {workflow['name']}")
                                continue
                            logging.info(f"Found {len(workflow_runs)} workflow runs for workflow {workflow['name']}")
                            for run in workflow_runs:
                                run_id = run['id']
                                try:
                                    jobs = github_api.get_jobs(repo_full_name, run_id)
                                    if not jobs:
                                        logging.info(f"No jobs found in workflow run {run_id}")
                                        continue
                                    logging.info(f"Found {len(jobs)} jobs in workflow run {run_id}")
                                    total_jobs_assessed += len(jobs)
                                    for job in jobs:
                                        logging.info(f"Job URL: {job['url']}")
                                        if not job.get('steps'):
                                            logging.info(f"Steps are empty for job {job['id']} in workflow run {run_id}. Logs may have expired.")
                                            total_empty_jobs += 1
                                            continue
                                        logging.info(f"Found {len(job['steps'])} steps in job {job['id']} in workflow run {run_id}")
                                        for step in job['steps']:
                                            total_actions_assessed += 1
                                            step_name = step['name']
                                            step_number = step['number']
                                            step_started_at = step.get('started_at')
                                            step_completed_at = step.get('completed_at')
                                            step_uses = step.get('uses', '').lower()
                                            step_url = job['url']
                                            step_html_url = job['html_url']
                                            duration = None
                                            if step_started_at and step_completed_at:
                                                start_time = datetime.strptime(step_started_at, '%Y-%m-%dT%H:%M:%SZ')
                                                end_time = datetime.strptime(step_completed_at, '%Y-%m-%dT%H:%M:%SZ')
                                                duration = (end_time - start_time).total_seconds()
                                            step_data = {
                                                "step_name": step_name,
                                                "repo_full_name": repo_full_name,
                                                "workflow_name": workflow['name'],
                                                "run_id": run_id,
                                                "job_id": job['id'],
                                                "step_number": step_number,
                                                "started_at": step_started_at,
                                                "completed_at": step_completed_at,
                                                "duration_seconds": duration,
                                                "url": step_url,
                                                "html_url": step_html_url
                                            }
                                            output_data.append(step_data)
                                            if step_name in step_names:
                                                step_name_totals[step_name] += duration
                                            if step_uses:
                                                logging.info(f"Step uses: {step_uses}")
                                            else:
                                                logging.info(f"Step name: {step_name}")
                                            if step_uses in ['docker/build-push-action@v5', 'docker/setup-qemu-action@v3.0.0']:
                                                if step_started_at and step_completed_at:
                                                    duration = end_time - start_time
                                                    logging.info(f"Repo: {repo_full_name}, Workflow: {workflow['name']}, Run ID: {run_id}, Step: {step_name}, Duration: {duration}")
                                                    if step_uses == 'docker/build-push-action@v5':
                                                        total_duration_build_push += duration
                                                    elif step_uses == 'docker/setup-qemu-action@v3.0.0':
                                                        total_duration_setup_qemu += duration
                                                else:
                                                    logging.warning(f"Missing start or end time for step {step_name} in repo {repo_full_name}")
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
        if min_duration > 0:
            output_data = [step for step in output_data if step['duration_seconds'] > min_duration]

        with open('steps_output.json', 'w') as f:
            json.dump(output_data, f, indent=4)

        # Log and write totals for specified step names
        if step_names:
            with open('step_name_totals.json', 'w') as f:
                json.dump(step_name_totals, f, indent=4)
            for step_name, total_duration in step_name_totals.items():
                logging.info(f"Total duration for {step_name}: {total_duration} seconds")

        logging.info(f"Total duration for docker/build-push-action@v5: {total_duration_build_push}")
        logging.info(f"Total duration for docker/setup-qemu-action@v3.0.0: {total_duration_setup_qemu}")
        logging.info(f"Total repositories assessed: {total_repositories_assessed}")
        logging.info(f"Total actions assessed: {total_actions_assessed}")
        logging.info(f"Total jobs assessed: {total_jobs_assessed}")
        logging.info(f"Total empty jobs (logs may have expired): {total_empty_jobs}")
    else:
        logging.error("Script execution failed. No summary information will be logged.")

if __name__ == "__main__":
    main()