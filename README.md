# 🚀 GitHub and Jenkins Build Auditor

The **Build Auditor** is a tool designed to help developers analyze and optimize their CI/CD workflows by tracking the duration of build steps. It supports both GitHub Actions and Jenkins pipelines, providing valuable insights into your build processes, helping identify bottlenecks, and improving build efficiency.

---

## ✨ Features

With the Build Auditor, you can:
- ⏱ **Analyze Build Durations**: Retrieve and evaluate the time taken by build steps in both GitHub Actions and Jenkins
- 🔍 **Filter Steps by Duration**: Focus on the most time-consuming pipeline steps
- 📊 **Aggregate Step Durations**: Identify unique steps and calculate their total durations
- 📝 **Generate Reports**: Export detailed results in **JSON format** for further analysis
- 🎨 **Colored Output**: Enhanced terminal output with color-coded messages for better readability
- 📈 **Monthly Summaries**: Generate monthly summaries of build times and frequencies

---

## 🛠 Prerequisites

Ensure you have:
- **Python 3.6+**
- A **GitHub Personal Access Token** (for GitHub analysis)
- **Jenkins Credentials** (for Jenkins analysis)

---

## 🔑 Authentication Setup

### GitHub Setup
1. **Log in to GitHub**: Visit [GitHub](https://github.com) and log in
2. **Navigate to Settings**: Click your profile picture → "Settings"
3. **Developer Settings**: Scroll down and select "Developer settings"
4. **Personal Access Tokens**: Choose "Tokens (fine-grained)"
5. **Generate New Token**:
   - Name the token
   - Set repository permissions:
     - **Contents**: `Read-only`
     - **Metadata**: `Read-only`
     - **Actions**: `Read-only`
6. **Copy the Token**: Save it securely

### Jenkins Setup
1. **Log in to Jenkins**
2. **User Settings**: Click your username → Configure
3. **API Token**: Generate a new API token
4. **Copy the Token**: Save it securely

### Environment Configuration
Create a `.env` file inside the project directory:
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

1. Clone the repository:
   ```bash
   git clone https://github.com/nickorefice/github-build-auditor.git
   cd github-build-auditor
   ```

2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

---

## ⚙️ Usage

To run the auditor:
```bash
# For GitHub analysis
python3 src/docker_build_time.py github

# For Jenkins analysis
python3 src/docker_build_time.py jenkins
```

### CLI Options:
- `--unique-steps`: Print unique step names to JSON
- `--filter-duration <seconds>`: Filter steps exceeding a specified duration
- `--force-continue`: Skip errors without prompting the user
- `--monthly-summary`: Generate monthly summary of step durations
- `--step-names-file <path>`: Path to a JSON file containing step names to calculate totals

### Example Commands:
```bash
# Generate unique steps for GitHub workflows
python3 src/docker_build_time.py github --unique-steps

# Analyze Jenkins builds with duration filter
python3 src/docker_build_time.py jenkins --filter-duration 300

# Generate monthly summary for GitHub
python3 src/docker_build_time.py github --monthly-summary

# Full analysis with specific steps
python3 src/docker_build_time.py github --step-names-file step_names.json --monthly-summary
```

### Output Color Coding:
The tool now uses color-coded output for better readability:
- 🟢 **Green**: Success messages and completions
- 🔵 **Blue**: Informational messages
- 🟡 **Yellow**: Warnings and prompts
- 🔴 **Red**: Errors
- 🔷 **Cyan**: Status updates and processing

---

## 📦 Example JSON Reports

### Stage Durations Output:
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

### Monthly Summary Output:
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
1. **Initial Analysis**:
   ```bash
   python src/docker_build_time.py github --unique-steps --filter-duration 10
   ```

2. **Create Step Names File**:
   Review the output and create a `step_names.json` with relevant steps.

3. **Detailed Analysis**:
   ```bash
   python src/docker_build_time.py github --step-names-file step_names.json --monthly-summary
   ```

4. **Compare Platforms**:
   Run analysis on both GitHub and Jenkins to compare build times.

---

## 📖 Documentation

### Available CLI Options:
- `ci_tool`: Choose between `github` or `jenkins`
- `--unique-steps`: Export unique step names
- `--filter-duration <seconds>`: Focus on steps exceeding a set duration
- `--force-continue`: Skip errors without interrupting execution
- `--monthly-summary`: Generate monthly summary reports
- `--step-names-file <path>`: Provide step names for totals calculation

---

## 🛡 Security

- Use tokens with minimal required permissions
- Store credentials securely in `.env` file
- Avoid committing tokens to version control

---

## 🤝 Contributing

We welcome contributions! To contribute:
1. Fork the repository
2. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-branch
   ```
5. Create a pull request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📧 Contact

For questions or support, open an [issue](https://github.com/nickorefice/github-build-auditor/issues).