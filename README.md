# 🚀 GitHub Build Auditor

The **GitHub Build Auditor** is a tool designed to help developers analyze and optimize their GitHub Actions workflows by tracking the duration of Docker build steps. Gain valuable insights into your CI/CD pipelines, identify bottlenecks, and improve build efficiency.

---

## ✨ Features

With the GitHub Build Auditor, you can:
- ⏱ **Analyze Docker Build Durations**: Retrieve and evaluate the time taken by Docker build steps.
- 🔍 **Filter Steps by Duration**: Focus on the most time-consuming pipeline steps.
- 📊 **Aggregate Step Durations**: Identify unique steps and calculate their total durations.
- 📝 **Generate Reports**: Export detailed results in **JSON format** for further analysis.

---

## 🛠 Prerequisites

Ensure you have:
- **Python 3.6+**
- A **GitHub Personal Access Token** with fine-grained permissions.

---

## 🔑 Creating a GitHub Personal Access Token

1. **Log in to GitHub**: Visit [GitHub](https://github.com) and log in.
2. **Navigate to Settings**: Click your profile picture → "Settings".
3. **Developer Settings**: Scroll down and select "Developer settings".
4. **Personal Access Tokens**: Choose "Tokens (fine-grained)".
5. **Generate New Token**:
   - Name the token.
   - Set repository permissions:
     - **Contents**: `Read-only`
     - **Metadata**: `Read-only`
     - **Actions**: `Read-only`
6. **Copy the Token**: Save it securely—once you leave, you cannot view it again.
7. **Add to Environment Variables to .env file inside project directory**:
   ```properties
   GITHUB_TOKEN=your_generated_token
   GITHUB_USERNAME=your_github_username
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
   python3 src/github_build_auditor.py
   ```

### CLI Options:
- `--unique-steps`: Print unique step names to JSON.
- `--filter-duration <seconds>`: Filter steps exceeding a specified duration (e.g., `--filter-duration 15`).
- `--force-continue`: Skip errors without prompting the user.
- `--step-names-file <path>`: Path to a JSON file containing step names to calculate totals.

### Example:
Create a `step_names.json` file with step names and rerun the auditor:
```bash
python3 src/github_build_auditor.py --step-names-file /path/to/step_names.json
```
**Sample step_names.json:**
```json
[
    "Build and push",
    "Docker Setup QEMU",
    "Build and push by digest",
    "Build and push Docker image on push",
    "Build and push Docker image on PR",
    "Set up QEMU"
]
```

**Sample Output:**
```json
{
  "Build and push": 7931.0,
  "Docker Setup QEMU": 93.0,
  "Build and push by digest": 722.0
}
```

---

## 📦 Example JSON Report

```json
[
   {
      "step_name": "Build and push",
      "repo_full_name": "user/repo1",
      "workflow_name": "CI",
      "run_id": 1234567890,
      "duration_seconds": 90.0,
      "html_url": "https://github.com/user/repo1/actions/runs/1234567890/job/1234567890"
   },
   {
      "step_name": "Docker buildx build",
      "repo_full_name": "user/repo2",
      "workflow_name": "CI",
      "run_id": 1234567891,
      "duration_seconds": 50.0,
      "html_url": "https://github.com/user/repo2/actions/runs/1234567891/job/1234567891"
   }
]
```

--- 

## 💡 Recommendations
To effectively use the GitHub Build Auditor, follow these steps:
1. Initial Run:
Run the script on as many repositories as possible with the `--unique-steps` option and possibly the `--filter-duration` option to identify as many steps involved with Docker builds.
```bash
python src/cli.py --unique-steps --filter-duration 10
```
2. Validate Step Names:
Review the output to validate which step names are related to Docker builds.
3. Create `step_names.json`:
Review the output to validate which step names are related to Docker builds.
4. Run with `--step-names-file`:
Run the script with the `--step-names-file` option to approximate the total duration of Docker build steps across repositories.
Example:
```bash
python src/cli.py --step-names-file src/step_names.json
```
5. Note on GitHub API:
Be aware that the GitHub API archives step names beyond 90 days old, so the total duration will not include those older steps.

---

## 📖 Documentation

### Available CLI Options:
- `--unique-steps`: Export unique step names.
- `--filter-duration <seconds>`: Focus on steps exceeding a set duration.
- `--force-continue`: Skip errors without interrupting execution.
- `--step-names-file <path>`: Provide step names for totals calculation.

---

## 🛡 Security

- Use a **GitHub Personal Access Token** with minimal permissions.
- Avoid committing your token to version control.

---

## 🤝 Contributing

We welcome contributions! To contribute:
1. Fork the repository.
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
5. Create a pull request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📧 Contact

For questions or support, open an [issue](https://github.com/nickorefice/github-build-auditor/issues).
