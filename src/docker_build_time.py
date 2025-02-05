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
@click.option("--force-continue", is_flag=True, help="(GitHub Only) Force continue even if there's an error")
@click.option("--filter-duration", type=int, default=0, help="(GitHub Only) Filter steps with duration longer than this value (in seconds)")
@click.option("--step-names-file", is_flag=True, help="Path to JSON file containing step names to calculate totals")
def main(ci_tool, unique_steps, force_continue, filter_duration, step_names_file):
    """ Executes the GitHub or Jenkins audit script based on the provided argument. """

    # Determine the script to run
    script = f"{ci_tool}_cli.py"
    print(script)


    # Check if the script exists
    if not os.path.exists(script):
        error_message = f"❌ Error: The script '{script}' was not found in the current directory."
        logging.error(error_message)
        click.echo(error_message)
        return

    click.echo(f"🔹 Running {ci_tool.capitalize()} audit...")

    # Construct the command
    cmd = ["python", script]

    if unique_steps:
        cmd.append("--unique-steps")

    if force_continue:
        cmd.append("--force-continue")

    if filter_duration > 0:
        cmd.extend(["--filter-duration", str(filter_duration)])

    if step_names_file:
        cmd.append("--step-names-file")

    # Execute the script with enhanced error handling
    # try:
    #     result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    #     # # Log and display output
    #     logging.info(result.stdout)
    #     click.echo(result.stdout)

    try:
        process = subprocess.Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, text=True)
        process.communicate()

    except subprocess.SubprocessError as e:
        error_message = f"❌ Error running {ci_tool} script: {e}"
        logging.error(error_message)
        click.echo(error_message)


if __name__ == "__main__":
    main()
