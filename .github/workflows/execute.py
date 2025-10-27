import os
import json
import subprocess
import sys
from datetime import datetime

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

def format_timestamp(dt):
    """Format datetime to ISO 8601 with milliseconds."""
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Trim to milliseconds

def calculate_elapsed(start_time, current_time):
    """Calculate elapsed time in seconds with millisecond precision."""
    elapsed = (current_time - start_time).total_seconds()
    return f"{elapsed:.3f}s"

def report_failure(tcid, script_file, input1, input2, expected, stdout, stderr, start_time, failure_time):
    prn = (os.environ.get("PRN") or "").strip()
    branch = (os.environ.get("BRANCH_NAME") or "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""

    # Calculate timing information
    timestamp_str = format_timestamp(failure_time)
    elapsed_str = calculate_elapsed(start_time, failure_time)

    # Build a concise, informative message
    header = f"❌ Test failure detected"
    details = (
        f"- **TCID**: {tcid}\n"
        f"- **Script**: {script_file}\n"
        f"- **Inputs**: [{input1}, {input2}]\n"
        f"- **Expected**: {expected}\n"
        f"- **Timestamp**: {timestamp_str} UTC\n"
        f"- **Elapsed Time**: {elapsed_str}\n"
        f"- **Run**: {run_url or 'N/A'}\n"
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
        title = f"{tcid} Failed at {timestamp_str}"
        gh_issue_create(title, body)
    else:
        # Fallback: print to logs if neither PR nor main branch context
        print(body)

    # Also append to step summary
    append_step_summary(f"- {header}: {tcid} ({script_file}) at {timestamp_str} (+{elapsed_str})")

def main():
    # Record execution start time with microsecond precision
    start_time = datetime.utcnow()
    start_timestamp = format_timestamp(start_time)
    
    print(f"🚀 Test execution started at: {start_timestamp} UTC")
    append_step_summary(f"## Test Execution Report\n\n**Started**: {start_timestamp} UTC\n")
    
    tcp_order = load_tcp_order()
    test_cases = load_test_cases()
    
    # Get canonical ordering from test-cases.json keys
    canonical_order = sorted(test_cases.keys())
    
    results = {}
    all_passed = True
    failure_count = 0

    for tcid in tcp_order:
        case = test_cases.get(tcid)
        if not case:
            failure_time = datetime.utcnow()
            print(f"Test case {tcid} not found in test-cases.json")
            results[tcid] = 1
            all_passed = False
            failure_count += 1
            continue
        script_file = case.get("script")
        if not script_file:
            failure_time = datetime.utcnow()
            print(f"No script defined for {tcid}")
            results[tcid] = 1
            all_passed = False
            failure_count += 1
            continue
        input1, input2 = case["input"]
        expected = case["output"]
        
        # Record test execution time
        test_start = datetime.utcnow()
        rc, out, err = run_test_script(script_file, input1, input2, expected)
        test_end = datetime.utcnow()
        test_duration = (test_end - test_start).total_seconds()
        
        results[tcid] = rc
        if rc != 0:
            all_passed = False
            failure_count += 1
            # Report immediately with precise timestamp
            report_failure(tcid, script_file, input1, input2, expected, out, err, start_time, test_end)
            print(f"❌ {tcid} failed after {test_duration:.3f}s")
        else:
            print(f"✅ {tcid} passed in {test_duration:.3f}s")

    # Reorder results dictionary according to canonical test-cases.json order
    ordered_results = {tcid: results.get(tcid, 0) for tcid in canonical_order}

    fault_dir = "test/fault-matrices"
    os.makedirs(fault_dir, exist_ok=True)
    existing = [
        f for f in os.listdir(fault_dir)
        if f.startswith("V") and f.endswith(".json") and f[1:-5].isdigit()
    ]
    next_num = 1 + max([int(f[1:-5]) for f in existing] or [0])
    out_path = os.path.join(fault_dir, f"V{next_num}.json")
    
    # Write fault matrix in canonical order
    with open(out_path, "w") as f:
        json.dump(ordered_results, f, indent=2)
    
    # Save TCP order to a temporary file for the workflow to use as Git note
    tcp_order_file = os.path.join(fault_dir, f"V{next_num}_tcp_order.txt")
    with open(tcp_order_file, "w") as f:
        f.write(f"TCP Order used for V{next_num} execution:\n")
        f.write(json.dumps(tcp_order, indent=2))
    
    # Calculate total execution time
    end_time = datetime.utcnow()
    end_timestamp = format_timestamp(end_time)
    total_duration = calculate_elapsed(start_time, end_time)
    
    print(f"\n📊 Test execution completed at: {end_timestamp} UTC")
    print(f"⏱️  Total duration: {total_duration}")
    print(f"✅ Passed: {len(tcp_order) - failure_count}/{len(tcp_order)}")
    print(f"❌ Failed: {failure_count}/{len(tcp_order)}")
    print(f"💾 Results saved to {out_path}")
    print(f"📋 TCP order saved to {tcp_order_file}")
    
    # Enhanced step summary with timing
    summary = (
        f"\n### Execution Summary\n\n"
        f"- **Completed**: {end_timestamp} UTC\n"
        f"- **Total Duration**: {total_duration}\n"
        f"- **Total Tests**: {len(tcp_order)}\n"
        f"- **Passed**: {len(tcp_order) - failure_count}\n"
        f"- **Failed**: {failure_count}\n"
        f"- **Success Rate**: {((len(tcp_order) - failure_count) / len(tcp_order) * 100):.1f}%\n"
    )
    append_step_summary(summary)

    # Set workflow output for all_passed
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"all_passed={'true' if all_passed else 'false'}\n")

if __name__ == "__main__":
    main()
