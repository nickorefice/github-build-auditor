import click
import subprocess


@click.command()
@click.option('--github', is_flag=True, help="Run the GitHub audit script")
@click.option('--jenkins', is_flag=True, help="Run the Jenkins audit script")
def main(github, jenkins):
    """ Executes either the GitHub or Jenkins script based on the provided flag. """

    if github and jenkins:
        click.echo("❌ Error: Please specify only one option: either --github or --jenkins")
        return

    if github:
        click.echo("🔹 Running GitHub script...")
        subprocess.run(["python", "github_cli.py"])  # ✅ Runs GitHub CLI as a separate process

    elif jenkins:
        click.echo("🔹 Running Jenkins script...")
        subprocess.run(["python", "jenkins_cli.py"])  # ✅ Runs Jenkins CLI as a separate process

    else:
        click.echo("❌ Error: You must specify either --github or --jenkins")

if __name__ == "__main__":
    main()
