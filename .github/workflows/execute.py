import os
import json
import subprocess

def load_tcp_order():
    with open("test/tcp.json") as f:
        return json.load(f)

def load_test_cases():
    with open("test/test-cases.json") as f:
        return json.load(f)

def run_script(script_path):
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=15
        )
        # Pass: True => 0, Fail => 1
        return 0 if "Pass: True" in result.stdout else 1
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        return 1

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
        script_path = os.path.join("test", "test-scripts", script_file)
        rc = run_script(script_path)
        results[tcid] = rc
        if rc != 0:
            all_passed = False
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
