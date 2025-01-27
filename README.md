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
7. **Add to Environment Variables**:
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

1. Set your GitHub Personal Access Token as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   ```

2. Run the auditor:
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

Sample report:
```json
[
  {
    "step_name": "Build and push",
    "repo_full_name": "nickorefice/db-demo",
    "workflow_name": "CI",
    "run_id": 12165501010,
    "duration_seconds": 90.0,
    "html_url": "https://github.com/nickorefice/db-demo/actions/runs/12165501010/job/33929599124"
  },
  {
    "step_name": "Build and push",
    "repo_full_name": "nickorefice/other-repo",
    "workflow_name": "CI",
    "run_id": 12165501010,
    "duration_seconds": 50.0,
    "html_url": "https://github.com/nickorefice/other-repo/actions/runs/12165501010/job/33929599404"
  }
]
```

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
