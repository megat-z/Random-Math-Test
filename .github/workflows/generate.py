import json
import os
import random

# --- CONFIGURATION ---
NUM_TESTS = 5  # Change this value to set the number of test cases

OPERATIONS = [
    ('+', lambda a, b: a + b),
    ('-', lambda a, b: a - b),
    ('*', lambda a, b: a * b),
    ('/', lambda a, b: a / b if b != 0 else None),
]

MIN_VAL, MAX_VAL = 1, 100

def random_case(idx):
    op_symbol, op_func = random.choice(OPERATIONS)
    a = random.randint(MIN_VAL, MAX_VAL)
    b = random.randint(MIN_VAL, MAX_VAL)
    output = op_func(a, b)
    # Ensure valid output for division
    while output is None:
        b = random.randint(1, MAX_VAL)
        output = op_func(a, b)
    case_id = f"TC{idx:03d}"
    script_name = f"{case_id}.py"
    return {
        "id": case_id,
        "input": f"{a} {op_symbol} {b}",
        "output": str(output),
        "script": script_name,
        "a": a,
        "b": b,
        "op": op_symbol
    }

def write_test_script(case):
    script_dir = os.path.join("test", "test-scripts")
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, case["script"])
    op_map = {'+': "+", '-': "-", '*': "*", '/': "/"}
    with open(script_path, "w") as f:
        f.write(
            f"# Auto-generated test script for {case['id']}\n"
            f"a = {case['a']}\n"
            f"b = {case['b']}\n"
            f"result = a {op_map[case['op']]} b\n"
            f"expected = {case['output']}\n"
            f"print('Input:', a, '{case['op']}', b)\n"
            f"print('Expected Output:', expected)\n"
            f"print('Actual Output:', result)\n"
            f"print('Pass:', abs(result - float(expected)) < 1e-9)\n"
        )

def main():
    test_cases = {}
    for idx in range(1, NUM_TESTS + 1):
        case = random_case(idx)
        test_cases[case["id"]] = {
            "input": case["input"],
            "output": case["output"],
            "script": case["script"]
        }
        write_test_script(case)
    os.makedirs("test", exist_ok=True)
    cases_path = os.path.join("test", "test-cases.json")
    with open(cases_path, "w") as f:
        json.dump(test_cases, f, indent=2)
    print(f"Generated {NUM_TESTS} test cases and scripts.")

if __name__ == "__main__":
    main()
