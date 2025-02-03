import os
import logging
import click
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("audit.log"),
        logging.StreamHandler(),
    ],
)


@click.command()
@click.option("--github", is_flag=True, help="Run the GitHub audit script")
@click.option("--jenkins", is_flag=True, help="Run the Jenkins audit script")
@click.option("--unique-steps", is_flag=True, help="Print unique step names to JSON")
@click.option("--force-continue", is_flag=True, help="Force continue even if there's an error")
@click.option("--filter-duration", type=int, default=0, help="Filter steps with duration longer than this value (in seconds)")
@click.option("--step-names-file", type=click.Path(exists=True), help="Path to JSON file containing step names to calculate totals")
def main(github, jenkins, unique_steps, force_continue, filter_duration, step_names_file):
    """ Executes the GitHub or Jenkins audit script based on the selected flag. """

    if github and jenkins:
        click.echo("❌ Error: Please specify only one option: either --github or --jenkins")
        return

    if github:
        click.echo("🔹 Running GitHub audit...")

        # Construct the command for github_cli.py
        cmd = ["python", "github_cli.py"]

        # Add optional parameters if specified
        if unique_steps:
            cmd.append("--unique-steps")
        if force_continue:
            cmd.append("--force-continue")
        if filter_duration > 0:
            cmd.extend(["--filter-duration", str(filter_duration)])
        if step_names_file:
            cmd.extend(["--step-names-file", step_names_file])

        # Run the GitHub CLI script with the parameters
        subprocess.run(cmd)

    elif jenkins:
        click.echo("🔹 Running Jenkins audit...")

        # Construct the command for jenkins_cli.py
        cmd = ["python", "jenkins_cli.py"]

        # Add optional parameters if specified
        if unique_steps:
            cmd.append("--unique-steps")

        # Run the Jenkins CLI script with the parameters
        subprocess.run(cmd)

    else:
        click.echo("❌ Error: You must specify either --github or --jenkins")


if __name__ == "__main__":
    main()
