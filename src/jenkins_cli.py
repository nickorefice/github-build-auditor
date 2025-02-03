import os
import logging
import json
import click
from collections import defaultdict
from dotenv import load_dotenv
from jenkins_api import JenkinsAPI


# Load environment variables
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
def main(unique_steps):
    JENKINS_URL = os.getenv("JENKINS_URL")
    JENKINS_USER = os.getenv("JENKINS_USER")
    JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

    if not JENKINS_USER:
        raise ValueError("Jenkins username must be set in the .env file")

    jenkins_api = JenkinsAPI()

    print("Fetching all Jenkins jobs...")
    jobs = jenkins_api.get_jobs()

    # Get all Jobs, Builds and Stages
    all_jobs_builds_stages = jenkins_api.all_jobs_stages_times(jobs)
    
    # Get Avg Build Time per Stage
    avg_job_time = jenkins_api.get_stage_averages(all_jobs_builds_stages)

    if unique_steps:
        # Unique Stage names
        unique_stage_names = jenkins_api.get_unique_stage_names(all_jobs_builds_stages)
        unique_stage_names = jenkins_api.output_json('Unique Stage Names', unique_stage_names, 'step_names.json')


    # Output JSON
    all_output_json = jenkins_api.output_json('General Job/Build Info', all_jobs_builds_stages, 'stage_durations.json')
    avg_output_summary = jenkins_api.output_json('Avg Build Time', avg_job_time, 'avg_stage_durations.json')

    print("Completed fetching all Jenkins Info, ENJOY!")
if __name__ == "__main__":
    main()