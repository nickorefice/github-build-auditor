# 🚀 GitHub and Jenkins Build Auditor

The **Build Auditor** is a tool designed to help developers analyze and optimize their CI/CD workflows by tracking the duration of build steps. It supports both **GitHub Actions** and **Jenkins pipelines**, providing valuable insights into your build processes, identifying bottlenecks, and improving build efficiency.

---

## ✨ Features

With the Build Auditor, you can:

- ⏱ **Analyze Build Durations**  
  Retrieve and evaluate the time taken by build steps in both GitHub Actions and Jenkins.
- 🔍 **Filter Steps by Duration**  
  Focus on the most time-consuming pipeline steps.
- 📊 **Aggregate Step Durations**  
  Identify unique steps and calculate their total durations.
- 📝 **Generate Reports**  
  Export detailed results in **JSON format** for further analysis.
- 🎨 **Colored Output**  
  Enjoy enhanced terminal output with color-coded messages for better readability.
- 📈 **Monthly Summaries**  
  Generate monthly summaries of build times and frequencies.
- 🌐 **Flexible Repository Fetch**  
  Use `--repos-file` or `--dump-repos` to manage which repositories you’re auditing.
- 🧭 **Custom Date Ranges**  
  Filter workflow runs with `--since` to analyze only those triggered on or after a specified date.

---

## 🛠 Prerequisites

1. **Python 3.6+**
2. **GitHub Personal Access Token** (for GitHub analysis)
3. **Jenkins Credentials** (for Jenkins analysis)

Ensure you have the correct **permissions** in your GitHub token:  
- **Contents**: `Read-only`  
- **Metadata**: `Read-only`  
- **Actions**: `Read-only`  

You may also need additional permissions if your workflows access private repositories or other GitHub features.

---

## 🔑 Authentication Setup

### GitHub Setup

1. **Log in to GitHub**: Visit [GitHub](https://github.com) and log in.  
2. **Navigate to Settings**: Click your profile picture → "Settings"  
3. **Developer Settings**: Scroll down and select "Developer settings"  
4. **Personal Access Tokens**: Choose "Tokens (fine-grained or classic)"  
5. **Generate New Token**  
   - Name the token (e.g. “Build Auditor Token”)  
   - Set minimal **Repository** permissions:  
     - **Contents**: `Read-only`  
     - **Metadata**: `Read-only`  
     - **Actions**: `Read-only`  
6. **Copy the Token**: Store it somewhere safe; do not commit it to version control.

### Jenkins Setup

1. **Log in to Jenkins**  
2. **User Settings**: Click your username → "Configure"  
3. **API Token**: Generate a new API token  
4. **Copy the Token**: Save it securely (e.g., in a password manager).

### Environment Configuration

Create a `.env` file in the project directory:

```properties
# GitHub Configuration
GITHUB_TOKEN=your_github_token

# Jenkins Configuration
JENKINS_URL=your_jenkins_url
JENKINS_USER=your_jenkins_username
JENKINS_TOKEN=your_jenkins_api_token
```

---

## 🚀 Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/nickorefice/github-build-auditor.git
   cd github-build-auditor
   ```
2. **Install the Required Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

---

## ⚙️ Usage

### Running the Auditor

```bash
# For GitHub analysis
python3 src/github_cli.py

# For Jenkins analysis
python3 src/jenkins_cli.py
```

#### CLI Options

| Option                     | Description                                                                                                   |
|----------------------------|---------------------------------------------------------------------------------------------------------------|
| `--unique-steps`           | Print unique step names to JSON                                                                              |
| `--filter-duration <s>`    | Filter steps exceeding a specified duration (in seconds)                                                     |
| `--force-continue`         | Skip errors without prompting the user                                                                       |
| `--monthly-summary`        | Generate a monthly summary of step durations                                                                  |
| `--step-names-file <path>` | Path to a JSON file containing step names to calculate totals                                                |
| `--skip-labels`            | Labels of jobs to skip. Multiple labels can be passed (e.g. `--skip-labels "self-hosted" --skip-labels "beta"`) |
| `--since <YYYY-MM-DD>`     | Only fetch workflow runs created on or after this date (GitHub only)                                         |
| `--repos-file <path>`      | Load GitHub repositories from a JSON file instead of querying all repos                                      |
| `--dump-repos`             | Dump all fetched GitHub repositories into `repositories.json` for offline management or review               |

#### Example Commands

```bash
# Generate unique steps for GitHub workflows
python3 src/github_cli.py --unique-steps

# Analyze Jenkins builds with duration filter
python3 src/jenkins_cli.py --filter-duration 300

# Generate monthly summary for GitHub
python3 src/github_cli.py --monthly-summary

# Full analysis with specific steps
python3 src/github_cli.py --step-names-file step_names.json --monthly-summary

# Skip Github jobs with specified labels
python3 src/github_cli.py --skip-labels "self-hosted" --skip-labels "another-label"

# Analyze only builds since 2024-01-01 for GitHub
python3 src/github_cli.py --since 2024-01-01

# Dump all repositories to a JSON file (GitHub only)
python3 src/github_cli.py --dump-repos

# Load your own set of repositories from repos.json (GitHub only)
python3 src/github_cli.py --repos-file repos.json
```

Use `--help` for either script (e.g. `python3 src/github_cli.py --help`) to see additional details.

---

## 📦 Example JSON Reports

### Stage Durations Output

```json
[
   {
      "step_name": "Build and push",
      "repo_full_name": "nickorefice/mastodon",
      "workflow_name": "github-build",
      "run_id": 8010151942,
      "job_id": 21880454544,
      "duration_seconds": 2476.0,
      "started_at": "2024-02-22T19:48:29Z",
      "completed_at": "2024-02-22T20:29:45Z",
      "url": "https://api.github.com/repos/nickorefice/mastodon/actions/jobs/21880454544",
      "html_url": "https://github.com/nickorefice/mastodon/actions/runs/8010151942/job/21880454544"
   }
]
```

### Monthly Summary Output

```json
{
   "2024-12": {
      "stages": {
         "Build and push": {
            "count": 4,
            "total_duration_seconds": 51.0
         }
      },
      "total_duration_seconds": 51.0
   }
}
```

---

## 💡 Recommendations

1. **Initial Analysis**  
   ```bash
   python3 src/github_cli.py --unique-steps --filter-duration 10
   ```
2. **Create Step Names File**  
   Review the output, then create a `step_names.json` with relevant steps or stage names.
3. **Detailed Analysis**  
   ```bash
   python3 src/github_cli.py --step-names-file step_names.json --monthly-summary
   ```
4. **Compare Platforms**  
   Run analysis on both GitHub and Jenkins to compare build times and identify differences.

---

## 📖 Documentation

### CLI Scripts

- **github_cli.py**  
  Primary entry point for GitHub-specific workflow analysis.

- **jenkins_cli.py**  
  Equivalent entry point for Jenkins-based pipeline analysis.

Use `--help` with any script to see all available flags and usage examples.

---

## 🛡 Security

- **Tokens with Minimal Permissions**  
  Only grant `repo: Actions, Contents, Metadata` or other essential scopes.  
- **Store Credentials Securely**  
  In `.env` (excluded from your VCS by default).  
- **Never Commit Tokens**  
  Rotate them regularly if needed.

---

## 🤝 Contributing

We welcome contributions from the community! To contribute:

1. **Fork the repository**  
2. **Create a new branch**:
   ```bash
   git checkout -b feature-branch
   ```
3. **Commit your changes**:
   ```bash
   git commit -m "Add new feature or fix"
   ```
4. **Push the branch**:
   ```bash
   git push origin feature-branch
   ```
5. **Open a pull request**  

We'll review your changes, offer feedback, and merge them if everything looks good.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). 

---

## 📧 Contact

For questions or support, please open an [issue](https://github.com/nickorefice/github-build-auditor/issues). We also welcome feature requests and feedback to continually improve this tool.

---

**Happy auditing of your CI/CD pipelines!**