import os
import logging
import click
import subprocess
import sys
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
@click.argument("ci_tool", type=click.Choice(["github", "jenkins"], case_sensitive=False))
@click.option("--unique-steps", is_flag=True, help="Print unique step names to JSON (Available for both scripts)")
@click.option("--force-continue", is_flag=True, help="Force continue even if there's an error")
@click.option("--filter-duration", type=int, default=0, help="Filter steps with duration longer than this value (in seconds)")
@click.option("--monthly-summary", is_flag=True, default=0, help="Provide a summary of how long each step took to run within a given month.")
@click.option("--step-names-file", type=click.Path(exists=True), default=None, required=False, help="Path to JSON file containing step names")
def main(ci_tool, unique_steps, force_continue, filter_duration, monthly_summary, step_names_file):
    """ Executes the GitHub or Jenkins audit script based on the provided argument. """

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the script to run with full path
    script = os.path.join(current_dir, f"{ci_tool}_cli.py")
    print(f"Script path: {script}")

    # Check if the script exists
    if not os.path.exists(script):
        error_message = f"❌ Error: The script '{script}' was not found."
        logging.error(error_message)
        click.echo(error_message)
        return

    # Construct the command
    cmd = [sys.executable, script]

    if unique_steps:
        cmd.append("--unique-steps")

    if force_continue:
        cmd.append("--force-continue")

    if filter_duration > 0:
        cmd.extend(["--filter-duration", str(filter_duration)])

    if monthly_summary:
        cmd.append("--monthly-summary")

    if step_names_file:
        cmd.extend(["--step-names-file", str(step_names_file)])

    click.echo(f"🔹 Running {ci_tool.capitalize()} audit...")
    print(f"🔹 Running command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd, 
            stdin=sys.stdin, 
            stdout=sys.stdout, 
            stderr=sys.stderr, 
            text=True,
            cwd=current_dir  # Set the working directory to the script's directory
        )
        process.communicate()

        if process.returncode != 0:
            error_message = f"❌ {ci_tool} script exited with code {process.returncode}"
            logging.error(error_message)
            click.echo(error_message)

    except subprocess.SubprocessError as e:
        error_message = f"❌ Error running {ci_tool} script: {e}"
        logging.error(error_message)
        click.echo(error_message)


if __name__ == "__main__":
    main()