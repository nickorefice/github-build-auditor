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
@click.option("--force-continue", is_flag=True, help="Continue execution even if Jenkins API fails")
@click.option('--filter-duration', type=int, default=0, help="Filter for steps with duration longer than the specified value in seconds")
@click.option("--step-names-file", is_flag=True, help="Path to JSON file containing step names to calculate totals")

def main(unique_steps, force_continue, filter_duration, step_names_file):
    JENKINS_URL = os.getenv("JENKINS_URL")
    JENKINS_USER = os.getenv("JENKINS_USER")
    JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

    if not JENKINS_USER:
        raise ValueError("Jenkins username must be set in the .env file")

    jenkins_api = JenkinsAPI()

    print("Fetching all Jenkins jobs...")

    # Initialize empty data structures in case of failure
    jobs = []
    all_jobs_builds_stages = {}

    try:
        jobs = jenkins_api.get_jobs()
        job_build_stage_data = {} 

        # Get Builds and Stages
        for job in jobs:
            job_name = job.get("name", "Unknown Job")  # Ensure job has a name
            build_stage_info = jenkins_api.all_jobs_stages_times([job])  # Pass as a list

        # Store in dictionary
        job_build_stage_data[job_name] = build_stage_info

        jenkins_api.output_json("General Job/Build Info", job_build_stage_data, "stage_durations.json")

        if unique_steps:
            unique_stage_names = jenkins_api.extract_unique_stage_names(job_build_stage_data)
            jenkins_api.output_json("Unique Stage Names", unique_stage_names, "step_names.json")

        if step_names_file:
            monthly_summary = jenkins_api.get_monthly_stage_summary(job_build_stage_data)
            jenkins_api.output_json("Monthly Totals", monthly_summary, "steps_output.json")

        
    except Exception as e:
        logging.error(f"Error fetching Jenkins API data: {e}")

        if not force_continue:
            raise SystemExit("Exiting due to Jenkins API failure.")

        print("Continuing execution with empty job data...")


    print("Completed fetching all Jenkins Info, ENJOY!")

if __name__ == "__main__":
    main()