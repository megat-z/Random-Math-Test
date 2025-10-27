import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Tuple, List

# Performance optimization: pre-load data once
_TCP_ORDER = None
_TEST_CASES = None

def load_tcp_order():
    global _TCP_ORDER
    if _TCP_ORDER is None:
        with open("test/tcp.json") as f:
            _TCP_ORDER = json.load(f)
    return _TCP_ORDER

def load_test_cases():
    global _TEST_CASES
    if _TEST_CASES is None:
        with open("test/test-cases.json") as f:
            _TEST_CASES = json.load(f)
    return _TEST_CASES

def run_test_script(script_name, input1, input2, expected):
    """Optimized test execution with minimal overhead."""
    script_path = os.path.join("test", "test-scripts", script_name)
    args = [str(input1), str(input2), str(expected)]
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True,
            text=True,
            timeout=15
        )
        return (0 if result.returncode == 0 else 1, result.stdout, result.stderr)
    except Exception as e:
        return (1, "", str(e))

def gh_env():
    """Cached environment setup."""
    env = os.environ.copy()
    token = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    return env

def gh_pr_comment(prn: str, body: str):
    """Non-blocking PR comment."""
    try:
        subprocess.run(
            ["gh", "pr", "comment", prn, "--body", body],
            check=False,
            capture_output=True,
            text=True,
            env=gh_env(),
            timeout=10
        )
    except Exception as e:
        print(f"[report] Failed to comment on PR #{prn}: {e}")

def gh_issue_create(title: str, body: str):
    """Non-blocking issue creation."""
    try:
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body],
            check=False,
            capture_output=True,
            text=True,
            env=gh_env(),
            timeout=10
        )
    except Exception as e:
        print(f"[report] Failed to create issue '{title}': {e}")

def format_timestamp(dt):
    """Format datetime to ISO 8601 with milliseconds."""
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def calculate_elapsed(start_time, current_time):
    """Calculate elapsed time in seconds with millisecond precision."""
    elapsed = (current_time - start_time).total_seconds()
    return f"{elapsed:.3f}s"

def report_failure(tcid, script_file, input1, input2, expected, stdout, stderr, start_time, failure_time):
    """Async failure reporting - non-blocking."""
    prn = (os.environ.get("PRN") or "").strip()
    branch = (os.environ.get("BRANCH_NAME") or "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""

    timestamp_str = format_timestamp(failure_time)
    elapsed_str = calculate_elapsed(start_time, failure_time)

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

    # Non-blocking issue/comment creation
    if prn:
        gh_pr_comment(prn, body)
    elif branch == "main" or branch.endswith("/main"):
        title = f"{tcid} Failed at {timestamp_str}"
        gh_issue_create(title, body)
    else:
        print(body)

def calculate_apfd(tcp_order: List[str], fault_results: Dict[str, int]) -> Tuple[float, Dict[str, any]]:
    """
    Calculate APFD (Average Percentage of Faults Detected) for the given TCP order.
    
    Formula: APFD = 1 - (sum(TF_i) / (n * m)) + 1/(2n)
    
    Where:
    - n = total number of test cases
    - m = total number of faults detected
    - TF_i = position of first test that detects fault i (1-indexed)
    
    Returns:
        (apfd_score, metadata_dict)
    """
    n = len(tcp_order)
    
    # Identify faults (failed tests) in execution order
    faults = [tcid for tcid in tcp_order if fault_results.get(tcid, 0) == 1]
    m = len(faults)
    
    if m == 0:
        # No faults detected - perfect (or no failures to prioritize)
        return 1.0, {
            "total_tests": n,
            "total_faults": 0,
            "first_fault_position": None,
            "average_fault_position": 0.0,
            "optimal_apfd": 1.0,
            "random_baseline": 0.5 + (1.0 / (2 * n)) if n > 0 else 0.5
        }
    
    # Calculate sum of fault detection positions
    tf_sum = 0
    first_fault_pos = None
    fault_positions = []
    
    for i, tcid in enumerate(tcp_order, start=1):
        if fault_results.get(tcid, 0) == 1:
            tf_sum += i
            fault_positions.append(i)
            if first_fault_pos is None:
                first_fault_pos = i
    
    # Calculate APFD
    apfd = 1.0 - (tf_sum / (n * m)) + (1.0 / (2 * n))
    
    # Calculate metadata
    avg_fault_pos = tf_sum / m if m > 0 else 0.0
    
    # Optimal APFD (if all faults detected first)
    optimal_tf_sum = sum(range(1, m + 1))
    optimal_apfd = 1.0 - (optimal_tf_sum / (n * m)) + (1.0 / (2 * n))
    
    # Random baseline estimate (faults distributed uniformly)
    random_baseline = 0.5 + (1.0 / (2 * n))
    
    metadata = {
        "total_tests": n,
        "total_faults": m,
        "first_fault_position": first_fault_pos,
        "average_fault_position": avg_fault_pos,
        "optimal_apfd": optimal_apfd,
        "random_baseline": random_baseline,
        "fault_positions": fault_positions
    }
    
    return apfd, metadata

def build_execution_report(execution_log: List[Dict], start_time, end_time, tcp_order: List[str], fault_results: Dict[str, int]):
    """Build comprehensive execution report table with APFD metrics."""
    total_duration = calculate_elapsed(start_time, end_time)
    
    # Calculate APFD
    apfd_score, apfd_meta = calculate_apfd(tcp_order, fault_results)
    
    report = [
        "## Test Execution Report",
        f"**Started**: {format_timestamp(start_time)} UTC",
        f"**Completed**: {format_timestamp(end_time)} UTC",
        f"**Total Duration**: {total_duration}",
        "",
        "### Execution Results (in order)",
        "",
        "| # | TCID | Status | Duration | Timestamp | Details |",
        "|---|------|--------|----------|-----------|---------|"
    ]
    
    for idx, log in enumerate(execution_log, 1):
        status_icon = "✅" if log['passed'] else "❌"
        tcid = log['tcid']
        duration = f"{log['duration']:.3f}s"
        timestamp = format_timestamp(log['timestamp'])
        details = log.get('script', 'N/A')
        
        report.append(f"| {idx} | {tcid} | {status_icon} | {duration} | {timestamp} | {details} |")
    
    # Summary statistics
    passed_count = sum(1 for log in execution_log if log['passed'])
    failed_count = len(execution_log) - passed_count
    success_rate = (passed_count / len(execution_log) * 100) if execution_log else 0
    
    report.extend([
        "",
        "### Summary",
        "",
        f"- **Total Tests**: {len(execution_log)}",
        f"- **Passed**: {passed_count} ✅",
        f"- **Failed**: {failed_count} ❌",
        f"- **Success Rate**: {success_rate:.1f}%",
        ""
    ])
    
    # APFD Metrics Section
    report.extend([
        "### 📊 APFD (Average Percentage of Faults Detected)",
        "",
        f"- **APFD Score**: **{apfd_score:.4f}** ({apfd_score * 100:.2f}%)",
    ])
    
    if apfd_meta["total_faults"] > 0:
        # Performance indicators
        if apfd_score >= 0.9:
            performance = "🟢 Excellent"
        elif apfd_score >= 0.7:
            performance = "🟡 Good"
        elif apfd_score >= 0.5:
            performance = "🟠 Moderate"
        else:
            performance = "🔴 Poor"
        
        improvement_over_random = ((apfd_score - apfd_meta['random_baseline']) / apfd_meta['random_baseline'] * 100) if apfd_meta['random_baseline'] > 0 else 0
        
        report.extend([
            f"- **Performance**: {performance}",
            f"- **First Fault Position**: #{apfd_meta['first_fault_position']} (out of {apfd_meta['total_tests']})",
            f"- **Average Fault Position**: {apfd_meta['average_fault_position']:.1f}",
            f"- **Optimal APFD** (all faults first): {apfd_meta['optimal_apfd']:.4f}",
            f"- **Random Baseline**: {apfd_meta['random_baseline']:.4f}",
            f"- **Improvement over Random**: {improvement_over_random:+.1f}%",
            "",
            "<details>",
            "<summary>📈 APFD Interpretation</summary>",
            "",
            "**APFD measures how quickly your test prioritization detects faults:**",
            "- **1.0** = Perfect (all faults detected immediately)",
            "- **0.9-0.99** = Excellent early fault detection",
            "- **0.7-0.89** = Good prioritization",
            "- **0.5-0.69** = Moderate effectiveness",
            "- **<0.5** = Below random ordering",
            "",
            f"**Fault positions in execution order**: {', '.join(f'#{p}' for p in apfd_meta['fault_positions'][:10])}" + 
            (f"... (+{len(apfd_meta['fault_positions']) - 10} more)" if len(apfd_meta['fault_positions']) > 10 else ""),
            "",
            "</details>",
        ])
    else:
        report.append("- **Status**: No faults detected (all tests passed) ✅")
    
    report.append("")
    
    return "\n".join(report)

def main():
    start_time = datetime.utcnow()
    print(f"🚀 Test execution started at: {format_timestamp(start_time)} UTC")
    
    # Pre-load data once
    tcp_order = load_tcp_order()
    test_cases = load_test_cases()
    canonical_order = sorted(test_cases.keys())
    
    # Execution tracking
    results = {}
    execution_log = []
    all_passed = True
    failure_count = 0

    # Execute tests in order (sequential for deterministic timing)
    for tcid in tcp_order:
        case = test_cases.get(tcid)
        if not case:
            failure_time = datetime.utcnow()
            print(f"❌ Test case {tcid} not found in test-cases.json")
            results[tcid] = 1
            execution_log.append({
                'tcid': tcid,
                'passed': False,
                'duration': 0.0,
                'timestamp': failure_time,
                'script': 'N/A'
            })
            all_passed = False
            failure_count += 1
            continue
            
        script_file = case.get("script")
        if not script_file:
            failure_time = datetime.utcnow()
            print(f"❌ No script defined for {tcid}")
            results[tcid] = 1
            execution_log.append({
                'tcid': tcid,
                'passed': False,
                'duration': 0.0,
                'timestamp': failure_time,
                'script': 'N/A'
            })
            all_passed = False
            failure_count += 1
            continue
            
        input1, input2 = case["input"]
        expected = case["output"]
        
        # Execute test with timing
        test_start = datetime.utcnow()
        rc, out, err = run_test_script(script_file, input1, input2, expected)
        test_end = datetime.utcnow()
        test_duration = (test_end - test_start).total_seconds()
        
        results[tcid] = rc
        passed = (rc == 0)
        
        # Log execution
        execution_log.append({
            'tcid': tcid,
            'passed': passed,
            'duration': test_duration,
            'timestamp': test_end,
            'script': script_file
        })
        
        if not passed:
            all_passed = False
            failure_count += 1
            # Real-time failure reporting (async, non-blocking)
            report_failure(tcid, script_file, input1, input2, expected, out, err, start_time, test_end)
            print(f"❌ {tcid} failed after {test_duration:.3f}s")
        else:
            print(f"✅ {tcid} passed in {test_duration:.3f}s")

    # Reorder results by canonical test-cases.json order
    ordered_results = {tcid: results.get(tcid, 0) for tcid in canonical_order}

    # Write fault matrix (single I/O operation)
    fault_dir = "test/fault-matrices"
    os.makedirs(fault_dir, exist_ok=True)
    
    # Optimized version detection
    existing = [int(f[1:-5]) for f in os.listdir(fault_dir) 
                if f.startswith("V") and f.endswith(".json") and f[1:-5].isdigit()]
    next_num = 1 + max(existing, default=0)
    
    out_path = os.path.join(fault_dir, f"V{next_num}.json")
    
    # Write fault matrix
    with open(out_path, "w") as f:
        json.dump(ordered_results, f, indent=2)
    
    # End timing
    end_time = datetime.utcnow()
    total_duration = calculate_elapsed(start_time, end_time)
    
    # Calculate APFD for console output
    apfd_score, apfd_meta = calculate_apfd(tcp_order, results)
    
    # Console summary
    print(f"\n📊 Test execution completed at: {format_timestamp(end_time)} UTC")
    print(f"⏱️  Total duration: {total_duration}")
    print(f"✅ Passed: {len(tcp_order) - failure_count}/{len(tcp_order)}")
    print(f"❌ Failed: {failure_count}/{len(tcp_order)}")
    print(f"📈 APFD Score: {apfd_score:.4f} ({apfd_score * 100:.2f}%)")
    print(f"💾 Results saved to {out_path}")
    
    # Build comprehensive step summary report with APFD
    report = build_execution_report(execution_log, start_time, end_time, tcp_order, results)
    
    # Write to step summary (single write)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "w") as f:
                f.write(report)
        except Exception as e:
            print(f"Warning: Failed to write step summary: {e}")

    # Set workflow output
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"all_passed={'true' if all_passed else 'false'}\n")
            f.write(f"apfd_score={apfd_score:.4f}\n")

if __name__ == "__main__":
    main()
