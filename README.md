# TCP-AW: Test Case Prioritization Automation Workflows

This repository contains an experimental framework for test case prioritization using quantum-inspired tensor networks, string distance metrics, and reinforcement learning. 

Automates test case management, prioritization, and fault detection reporting via GitHub Actions and Google Apps Script integration.

## 🚀 Getting Started: Step-by-Step Guide

Follow these instructions to set up the full workflow from forking to automated test case prioritization.

---

### 1. **Use This Template**

- Click the [**Use this template**](https://github.com/new?template_name=TCP-AW&template_owner=megat-z) button at the top-right of this repository page to create a new repository based on this template.
- *(Optional)* Alternatively, click the **Fork** button to create a fork of this repository under your account.
- *(Optional)* You can also `git clone` this repository and push it to a new repository if you prefer manual setup.

---

### 2. **Generate a Personal Access Token (PAT)**

- Go to [GitHub > Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
- Click "Generate new token".
- Select scope: `repo` (at minimum).
- Copy the generated token (you’ll need it in step 5).

---

### 3. **Set Up Google Apps Script with Code.gs**

- Create a new project in [Google Apps Script](https://script.google.com).
- Copy the contents of `Code.gs` from this repository.
- Paste it into your Apps Script editor.

---

### 4. **Configure Script Properties**

- In Apps Script, go to `Project Settings` > `Script Properties`.
- Add the following properties:
  - `GITHUB_PAT`: Paste your Personal Access Token from step 2.
  - `DISPATCH_URL`: Paste the dispatch URL:
    ```
    https://api.github.com/repos/<your-username>/<your-repo-name>/dispatches
    ```
    Replace `<your-username>` and `<your-repo-name>` accordingly.

---

### 5. **Deploy as a Web App**

- In the Apps Script editor, click `Deploy` > `New deployment`.
- Choose "Web app".
- Set access to "Anyone" or "Anyone, even anonymous".
- Deploy.  
- Copy the deployment URL (you’ll need it for the webhook).

---

### 6. **Add a Webhook to Your GitHub Repo**

- Go to your forked repo’s **Settings** > **Webhooks** > **Add webhook**.
- Paste your Web App URL from step 5.
- Set **Content type** to `application/json`.
- Activate the webhook (enable it).
- Save.

---

### 7. **Edit `test-cases.json`**

- Modify or add test cases in `test/test-cases.json` as needed.
- Each commit or push to this file will trigger the workflow.
- After each commit to `test-cases.json`, check these files:
  - `test/string-distances/input.json`
  - `test/string-distances/output.json`
- These contain normalized string distance matrices for inputs and outputs.

---

### 8. **Confirm Setup on GitHub Actions**

- Go to your repo’s **Actions** tab.
- Check that the workflow named "Calculate Distance Matrices" runs after changes to `test-cases.json`.
- View logs for errors or confirmation.

---

### 9. **Add Your Project Code & Test Scripts**

- Place your main project code at the repository root or as desired.
- Add individual test case scripts in the `test/test-scripts/` directory.  
- Each file should match the naming or script property in your `test-cases.json`.

---

### 10. **Review Fault Matrices on Each Commit**

- Any other commit is will:
  - Read from `fault-matrices` folder (if any)
  - Print (log/output) the prioritization order for test execution.
  - Start executing the test scripts as listed in `test-cases.json`, following the predicted prioritization order.
  - Record and update fault detection results in a new versioned matrix (e.g., `vN+1.json`).
  - This enables continuous prioritization and APFD tracking as your codebase evolves.

---

## 📝 Example Workflow

1. Edit `test/test-cases.json` and commit changes.
2. Webhook triggers Google Apps Script, which dispatches to GitHub Actions.
3. GitHub Actions runs `setup.py`, computes distance matrices, and updates results.
4. Review matrices and workflow status in the Actions tab.
5. **On non-`test-cases.json` commits, automated test prioritization and execution occurs, updating and logging fault detection matrices (`vN.json`).**
6. Iterate and improve test coverage and prioritization.

---

## 🛠 Troubleshooting

- **Webhook not triggering?**  
  Check that the webhook URL is correct and content type is `application/json`.
- **No workflow runs?**  
  Ensure your PAT and dispatch URL are set correctly in Apps Script properties.
- **Missing test scripts warning?**  
  Add missing scripts to `test/test-scripts/` or update `test-cases.json` accordingly.
- **Distance matrices not updating?**  
  Confirm changes are being committed to `test-cases.json`.
- **Prioritization or execution not running after other commits?**  
  Check automation logs and ensure prioritization scripts are enabled and reading latest matrices.

---

## 📚 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Apps Script Documentation](https://developers.google.com/apps-script/)
- [RapidFuzz Documentation](https://maxbachmann.github.io/RapidFuzz/)

---

## 👩‍🔬 About the Project

This framework aims to push the boundaries of automated test prioritization in CI/CD environments, leveraging quantum-inspired tensor networks for optimal APFD. Contributions and research feedback welcome!
