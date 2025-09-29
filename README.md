# Random Math Test

_Automated math test generation and prioritization, powered by test automation templates from [TCP-AW](https://github.com/megat-z/TCP-AW)._

---

## 🚀 Overview

Random Math Test is a template-based framework for generating, managing, and prioritizing simple arithmetic test cases. This project leverages the automation workflows and methodologies pioneered in [TCP-AW: Test Case Prioritization Automation Workflows](https://github.com/megat-z/TCP-AW), adapted for educational and assessment environments.

- **Automates math test case management and prioritization**
- **Provides actionable feedback via GitHub Actions**
- **Integrates with Google Apps Script for advanced dispatches**

---

## 📦 Getting Started

### 1. **Create Your Own Math Test Repo**

- Click [**Use this template**](https://github.com/new?template_name=Random-Math-Test&template_owner=megat-z) OR fork this repository.
- Alternatively, clone and push to a new repo manually.

### 2. **Follow the TCP-AW Automation Setup**

This project uses the same workflow template as TCP-AW. Refer to [TCP-AW's README](https://github.com/megat-z/TCP-AW#readme) for detailed setup:

- **Generate a GitHub Personal Access Token (PAT)**
- **Set up Google Apps Script with the provided Code.gs**
- **Configure script properties** (`GITHUB_PAT`, `DISPATCH_URL`)
- **Deploy as a Web App**
- **Add your Apps Script Webhook to GitHub**

### 3. **Edit Math Test Cases**

- All test cases live in `test/test-cases.json`.
- Each commit to this file triggers prioritization and updates associated matrices:
  - `test/string-distances/input.json`
  - `test/string-distances/output.json`

### 4. **Add Your Math Problem Scripts**

- Place your math problem solution scripts in `test/test-scripts/`.
- The script filenames should correspond to entries in `test-cases.json`.

### 5. **Review Prioritization and Results**

- Every commit updates prioritization order and fault matrices (`fault-matrices/vN.json`).
- Logs and workflow status are visible in your repo's **Actions** tab.

---

## 🛠 Troubleshooting

- **Webhook not working?**  
  Double-check your Web App URL and content type (`application/json`).
- **No workflow runs?**  
  Ensure your PAT and dispatch URL are set correctly.
- **Missing test scripts warning?**  
  Match filenames in `test/test-scripts/` with your `test-cases.json`.
- **Distance matrices not updating?**  
  Confirm commits are made to `test-cases.json`.

---

## 📚 References

- [TCP-AW: Test Case Prioritization Automation Workflows](https://github.com/megat-z/TCP-AW)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Apps Script Documentation](https://developers.google.com/apps-script/)
- [RapidFuzz Documentation](https://maxbachmann.github.io/RapidFuzz/)

---

## 👩‍🔬 About

Random Math Test aims to make math test generation, execution, and prioritization effortless for educators, students, and researchers. Built on advanced automation and prioritization workflows from TCP-AW, it provides a robust, open-source foundation for continuous math assessment improvement.

---

**Inspired by [TCP-AW](https://github.com/megat-z/TCP-AW).**
