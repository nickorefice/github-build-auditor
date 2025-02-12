import os
import requests
import logging
import jenkins
import json
import datetime
from collections import defaultdict
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")


class JenkinsAPI:
    def __init__(self):
        self.server = jenkins.Jenkins(JENKINS_URL, username=JENKINS_USER, password=JENKINS_TOKEN)
        self.user = self.server.get_whoami()
        self.version = self.server.get_version()
        self.auth = (JENKINS_USER, JENKINS_TOKEN)
        self.headers = {"Accept": "application/json"}
        logging.info(f"Connected to Jenkins {JENKINS_URL} as {self.user['fullName']} (Version: {self.version})")

    def get_jobs(self):
        """ Fetch all Jenkins jobs """
        try:
            jobs = self.server.get_jobs()
            pipeline_jobs = self.filter_workflow_jobs(jobs)
            return pipeline_jobs
        except jenkins.JenkinsException as e:
            logging.error(f"Error retrieving jobs: {e}")
            return []
        

    def get_job_builds(self, job_name):
        """ Fetch all builds for a given job """
        try:
            job_info = self.server.get_job_info(job_name)
            return [
                {"number": build["number"], "url": build["url"], "result": build.get("result", "IN_PROGRESS")}
                for build in job_info["builds"]
            ]
        except jenkins.JenkinsException as e:
            logging.error(f"Error retrieving builds for {job_name}: {e}")
            return []

    def get_build_info(self, job_name, build_number):
        """ Fetch specific build details """
        try:
            build_info = self.server.get_build_info(job_name, build_number)
            return build_info
        except jenkins.JenkinsException as e:
            logging.error(f"Error retrieving build #{build_number} for {job_name}: {e}")
            return {}
        
    
    def get_pipeline_stages_and_duration(self, job_name, build_number):
        """ Fetch all pipeline stages and their durations using wfapi/describe. """
        url = f"{JENKINS_URL}/job/{job_name}/{build_number}/wfapi/describe"
        response = requests.get(url, auth=self.auth, headers=self.headers)

        if response.status_code != 200:
            logging.error(f"Error fetching stage data for {job_name} build {build_number}: {response.status_code}")
            return []

        data = response.json()

        return [
            {
                **stage,  # ✅ Include all original fields
                "duration_seconds": (stage.get("durationMillis", 0) + stage.get("queueDurationMillis", 0)) / 1000,
                "started_at": stage.get("startTimeMillis"),
                "formatted_started_at": self.format_timestamp(stage.get("startTimeMillis")),
                "completed_at": stage.get("startTimeMillis", 0) + stage.get("durationMillis", 0),
            }
            for stage in data.get("stages", [])
        ]
        
    def format_timestamp(self, millis):
        """ Convert milliseconds timestamp to a human-readable date-time format. """
        if not millis:
            return None
        dt = datetime.datetime.fromtimestamp(millis / 1000.0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def filter_workflow_jobs(self, jobs):
        """ 
        Filter jobs to only include Jenkins Workflow Jobs.
        Logs jobs that are not of type 'org.jenkinsci.plugins.workflow.job.WorkflowJob'.
        """
        workflow_jobs = []

        for job in jobs:
            if job.get("_class") == "org.jenkinsci.plugins.workflow.job.WorkflowJob":
                workflow_jobs.append(job)
            else:
                logging.warning(f"Skipping non-pipeline job: {job.get('name', 'Unknown Job')} (Class: {job.get('_class')})")

        return workflow_jobs

    def get_build_stage_data(self, job):
        """ Get builds and stage data for a specific job """
        build_data = []
        pipeline_name = job.get("fullname", job.get("name", "Unknown Pipeline"))  # ✅ Extract pipeline name

        builds = self.get_job_builds(job["name"])
        if not isinstance(builds, list):  # ✅ Ensure builds is a valid list
            logging.error(f"Invalid build data for job {job['name']}: {builds}")
            return []

        for build in builds:
            stages = self.get_pipeline_stages_and_duration(job["name"], build["number"])

            if not isinstance(stages, list):  # ✅ Ensure stages is a valid list
                logging.error(f"Invalid stage data for job {job['name']} build {build['number']}: {stages}")
                continue

            for stage in stages:
                if isinstance(stage, dict):  # ✅ Ensure `stage` is a dictionary before unpacking
                    build_data.append({
                        "pipeline_name": pipeline_name, # ✅ Include pipeline name
                        **job, 
                        **build, 
                        **stage
                                                                
                    })
                else:
                    logging.error(f"Skipping invalid stage entry in job {job['name']} build {build['number']}: {stage}")

        return build_data

    def all_jobs_stages_times(self, jobs, filter_duration=None):
        """ Fetch and process job build and stage data. """
        workflow_jobs = self.filter_workflow_jobs(jobs)
        output_summary = [
            data for job in workflow_jobs
            for data in self.get_build_stage_data(job)
            if isinstance(data, dict) and (filter_duration is None or data.get("duration_seconds", 0) > filter_duration)  # ✅ Ensure valid dictionary before filtering
        ]
        return output_summary
    
    def output_json(self, print_message, content, file_name):
        # Save to JSON file
        with open(file_name, "w") as json_file:
            try:
                json.dump(content, json_file, indent=4)
                print(f"✅ {print_message} successfully written to {file_name}")
            except Exception as e:
                logging.error(f"Error writing JSON output: {e}")

    def extract_unique_stage_names(self, job_data):
        """ Extracts unique stage names from the given Jenkins job data. """
        unique_names = set()  # Use a set to store unique names

        for job, stages in job_data.items():
            for stage in stages:
                stage_name = stage.get("name")  # Extract name safely
                if stage_name:
                    unique_names.add(stage_name)  # Add to set to ensure uniqueness

        return list(unique_names)  # Convert back to list for output
    
    def load_step_names(self, step_names_file):
        """ Loads step names from a JSON file if provided, else returns an empty list. """
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

    def get_monthly_stage_summary(self, data, filter_steps=None):
        """
        Aggregates the total duration and count of each stage for each month.

        :param data: Dictionary containing Jenkins job build information.
        :return: Dictionary with monthly summaries, including count, total duration per stage, and overall total duration.
        """
        monthly_summary = defaultdict(lambda: {"stages": defaultdict(lambda: {"count": 0, "total_duration": 0}), "total_duration_seconds": 0})

        for pipeline, stages in data.items():  # Iterate through each pipeline
            for stage in stages:
                start_time = stage.get("started_at")
                if not start_time:
                    continue  # Skip if timestamp is missing

                # Convert to datetime
                try:
                    stage_date = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue  # Skip if parsing fails

                month_key = stage_date.strftime("%Y-%m")  # Format as YYYY-MM for grouping
                stage_name = stage.get("name", "Unknown Stage")

                 # ✅ Filter stages based on `filter_steps` list
                if filter_steps and stage_name not in filter_steps:
                    continue  # Skip stages not in the filter list

                duration = stage.get("duration_seconds", 0)

                # ✅ Increment count of stage executions
                monthly_summary[month_key]["stages"][stage_name]["count"] += 1

                # ✅ Sum the total duration for the stage
                monthly_summary[month_key]["stages"][stage_name]["total_duration"] += duration

                # ✅ Add to overall total duration for the month
                monthly_summary[month_key]["total_duration_seconds"] += duration

        # Convert defaultdict to regular dict for JSON-friendly output
        return {
            month: {
                "stages": {
                    stage: {
                        "count": data["stages"][stage]["count"],
                        "total_duration_seconds": round(data["stages"][stage]["total_duration"], 3)  # Round for readability
                    }
                    for stage in data["stages"]
                },
                "total_duration_seconds": round(data["total_duration_seconds"], 3)
            }
            for month, data in monthly_summary.items()
        }


    
if __name__ == "__main__":
    jenkins_api = JenkinsAPI()

    print("Fetching all Jenkins jobs...")
    # Get Jobs
    jobs = jenkins_api.get_jobs()
    job_build_stage_data = {} 
    # Get Builds and Stages
    for job in jobs:
        job_name = job.get("name", "Unknown Job")  # Ensure job has a name
        build_stage_info = jenkins_api.all_jobs_stages_times([job])  # Pass as a list

        # Store in dictionary
        job_build_stage_data[job_name] = build_stage_info

    # Output JSON
    all_output_json = jenkins_api.output_json('General Job/Build Info', job_build_stage_data, 'stage_durations.json')