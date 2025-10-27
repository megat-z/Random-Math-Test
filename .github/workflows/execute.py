import os
import json
import subprocess
import sys

def load_tcp_order():
    with open("test/tcp.json") as f:
        return json.load(f)

def load_test_cases():
    with open("test/test-cases.json") as f:
        return json.load(f)

def run_test_script(script_name, input1, input2, expected):
    script_path = os.path.join("test", "test-scripts", script_name)
    args = [str(input1), str(input2), str(expected)]
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True,
            text=True,
            timeout=15
        )
        rc = 0 if result.returncode == 0 else 1
        return rc, result.stdout, result.stderr
    except Exception as e:
        msg = f"Error running {script_name} with {args}: {e}"
        print(msg)
        return 1, "", msg

def gh_env():
    env = os.environ.copy()
    # Prefer GH_TOKEN if set, else fall back to GITHUB_TOKEN if present
    token = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    return env

def gh_pr_comment(prn: str, body: str):
    try:
        subprocess.run(
            ["gh", "pr", "comment", prn, "--body", body],
            check=False,
            capture_output=True,
            text=True,
            env=gh_env(),
        )
    except Exception as e:
        print(f"[report] Failed to comment on PR #{prn}: {e}")

def gh_issue_create(title: str, body: str):
    try:
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body],
            check=False,
            capture_output=True,
            text=True,
            env=gh_env(),
        )
    except Exception as e:
        print(f"[report] Failed to create issue '{title}': {e}")

def append_step_summary(text: str):
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a") as f:
                f.write(text + "\n")
        except Exception:
            pass

def report_failure(tcid, script_file, input1, input2, expected, stdout, stderr):
    prn = (os.environ.get("PRN") or "").strip()
    branch = (os.environ.get("BRANCH_NAME") or "").strip()
    attempt = (os.environ.get("EXECUTION_ATTEMPT") or "1").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""

    # Build a concise, informative message
    header = f"❌ Test failure detected (attempt {attempt})"
    details = (
        f"- TCID: {tcid}\n"
        f"- Script: {script_file}\n"
        f"- Inputs: [{input1}, {input2}]\n"
        f"- Expected: {expected}\n"
        f"- Run: {run_url or 'N/A'}\n"
    )
    logs = ""
    if stdout:
        logs += f"\n<details><summary>stdout</summary>\n\n```\n{stdout.strip()}\n```\n</details>"
    if stderr:
        logs += f"\n<details><summary>stderr</summary>\n\n```\n{stderr.strip()}\n```\n</details>"

    body = f"{header}\n\n{details}{logs}"

    # Report to PR or Issues without stopping execution
    if prn:
        gh_pr_comment(prn, body)
    elif branch == "main" or branch.endswith("/main"):
        title = f"[Attempt {attempt}] Failed test: {tcid}"
        gh_issue_create(title, body)
    else:
        # Fallback: print to logs if neither PR nor main branch context
        print(body)

    # Also append to step summary
    append_step_summary(f"- {header}: {tcid} ({script_file})")

def main():
    tcp_order = load_tcp_order()
    test_cases = load_test_cases()
    results = {}
    all_passed = True

    for tcid in tcp_order:
        case = test_cases.get(tcid)
        if not case:
            print(f"Test case {tcid} not found in test-cases.json")
            results[tcid] = 1
            all_passed = False
            continue
        script_file = case.get("script")
        if not script_file:
            print(f"No script defined for {tcid}")
            results[tcid] = 1
            all_passed = False
            continue
        input1, input2 = case["input"]
        expected = case["output"]
        rc, out, err = run_test_script(script_file, input1, input2, expected)
        results[tcid] = rc
        if rc != 0:
            all_passed = False
            # Report immediately, do not halt
            report_failure(tcid, script_file, input1, input2, expected, out, err)

    fault_dir = "test/fault-matrices"
    os.makedirs(fault_dir, exist_ok=True)
    existing = [
        f for f in os.listdir(fault_dir)
        if f.startswith("V") and f.endswith(".json") and f[1:-5].isdigit()
    ]
    next_num = 1 + max([int(f[1:-5]) for f in existing] or [0])
    out_path = os.path.join(fault_dir, f"V{next_num}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")

    # Set workflow output for all_passed
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"all_passed={'true' if all_passed else 'false'}\n")

if __name__ == "__main__":
    main()
