import os
import requests
import logging
import jenkins
import json
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
            return [{"name": job["name"], "url": job["url"]} for job in jobs]
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
            logging.error(f"Error fetching stage data (this is not a pipeline job): {response.status_code}")
            return []

        data = response.json()
        return [
            {
                "stage_name": stage.get("name", "Unknown Stage"),
                "duration_ms": stage.get("durationMillis", 0) + stage.get("queueDurationMillis", 0)
            }
            for stage in data.get("stages", [])
        ]
    
    def all_jobs_stages_times(self, jobs):
        """ Fetch all pipeline stages and their durations for all jobs and builds. """
        output_summary = [
            {
                "job_name": job["name"],
                "build_number": build["number"],
                "stage_name": stage["stage_name"],
                "duration_ms": stage["duration_ms"]
            }
            for job in jobs
            for build in self.get_job_builds(job["name"])
            for stage in self.get_pipeline_stages_and_duration(job["name"], build["number"])
            if stage  # Ensures only valid stages are included
        ]
        
        return output_summary
    
    def output_json(self, print_message, content, file_name):
        # Save to JSON file
        with open(file_name, "w") as json_file:
            json.dump(content, json_file, indent=4)
        print(f"✅ {print_message} successfully written to {file_name}")

    def get_stage_averages(self, all_stage_data):
        # Dictionary to store total duration and count per stage
        stage_totals = defaultdict(lambda: {"total_duration_in_ms": 0, "count": 0})
        print(stage_totals)
        # Iterate through all stage records and accumulate durations
        for entry in all_stage_data:
            stage_name = entry["stage_name"]
            duration_ms = entry["duration_ms"]

            stage_totals[stage_name]["total_duration_in_ms"] += duration_ms
            stage_totals[stage_name]["count"] += 1

        # Compute the average duration per stage
        average_stage_durations = {
            stage: round(totals["total_duration_in_ms"] / totals["count"], 2) 
            for stage, totals in stage_totals.items()
        }
        # Print results
        print("\n🚀 Average Stage Durations Across Builds:")
        for stage, avg_duration in average_stage_durations.items():
            print(f"🔹 {stage} - Average Duration: {avg_duration:.2f} ms")
        return average_stage_durations
    
    def get_unique_stage_names(self, all_stage_data):
        return list({item["stage_name"] for item in all_stage_data})


    
if __name__ == "__main__":
    jenkins_api = JenkinsAPI()

    print("Fetching all Jenkins jobs...")
    jobs = jenkins_api.get_jobs()

    # Get all Jobs, Builds and Stages
    all_jobs_builds_stages = jenkins_api.all_jobs_stages_times(jobs)
    
    # Get Avg Build Time per Stage
    avg_job_time = jenkins_api.get_stage_averages(all_jobs_builds_stages)

    # Output JSON
    all_output_json = jenkins_api.output_json('General Job/Build Info', all_jobs_builds_stages, 'stage_durations.json')
    avg_output_summary = jenkins_api.output_json('Avg Build Time', avg_job_time, 'avg_stage_durations.json')
