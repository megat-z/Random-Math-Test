import json
import os
import random

NUM_TESTS = 25
OPERATIONS = [
    ('add.py'),
    ('sub.py'),
    ('mul.py'),
    ('div.py')
]
MIN_VAL, MAX_VAL = 1, 100

def random_case(idx):
    script_name = random.choice(OPERATIONS)
    a = random.randint(MIN_VAL, MAX_VAL)
    b = random.randint(MIN_VAL, MAX_VAL)
    # For div, avoid zero division
    output = random.randint(MIN_VAL, MAX_VAL)
    case_id = f"TC{idx:02d}"
    return {
        "id": case_id,
        "input": [a, b],
        "output": output,
        "script": script_name
    }

def main():
    test_cases = {}
    os.makedirs("test/test-scripts", exist_ok=True)
    for idx in range(1, NUM_TESTS + 1):
        case = random_case(idx)
        test_cases[case["id"]] = {
            "input": case["input"],
            "output": case["output"],
            "script": case["script"],
        }
    os.makedirs("test", exist_ok=True)
    cases_path = os.path.join("test", "test-cases.json")
    with open(cases_path, "w") as f:
        json.dump(test_cases, f, indent=2)
    print(f"Generated {NUM_TESTS} test cases.")

if __name__ == "__main__":
    main()
