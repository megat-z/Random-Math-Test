import json
import os
import random
import sys
from typing import Tuple, Union

PROB_DIST = 0.5 # 0.0 -> 1.0
NUM_TESTS = 10 # Any Integer
OPERATIONS = [
    'add.py',
    'sub.py',
    'mul.py',
    'div.py'
]
MIN_VAL, MAX_VAL = 1, 100

def pick_operation() -> str:
    return random.choice(OPERATIONS)

def generate_inputs(op: str) -> Tuple[int, int]:
    # Currently all ops use two ints in [MIN_VAL, MAX_VAL]
    a = random.randint(MIN_VAL, MAX_VAL)
    b = random.randint(MIN_VAL, MAX_VAL)
    # For division, avoid zero division (already avoided by MIN_VAL=1, but keep here for clarity)
    if op == 'div.py' and b == 0:
        b = random.randint(MIN_VAL, MAX_VAL) or 1
    return a, b

def compute_correct_output(op: str, a: int, b: int) -> Union[int, float]:
    if op == 'add.py':
        return a + b
    if op == 'sub.py':
        return a - b
    if op == 'mul.py':
        return a * b
    if op == 'div.py':
        # Division yields float
        return a / b
    # Fallback, though all ops are covered
    return a + b

def generate_faulty_output(op: str, a: int, b: int, correct: Union[int, float]) -> Union[int, float]:
    # Produce an output that is intentionally wrong, respecting each op’s typical type
    if op in ('add.py', 'sub.py', 'mul.py'):
        # Integers for these ops
        # Try until we get something different; very low chance of looping long
        for _ in range(10):
            wrong = random.randint(MIN_VAL, MAX_VAL)
            if wrong != correct:
                return wrong
        # As a last resort, perturb by 1
        return correct + 1 if isinstance(correct, int) else int(correct) + 1
    else:
        # div.py accepts ints or floats; script compares with isclose for floats
        # Choose an int in the range that is not "isclose" to the true float result
        # Using a simple inequality will be enough in practice since correct is usually non-integer
        wrong = random.randint(MIN_VAL, MAX_VAL)
        # If the result happens to be an integer equal to wrong, shift it
        if isinstance(correct, (int, float)) and abs(float(wrong) - float(correct)) < 1e-12:
            wrong += 1
        return wrong

def random_case(idx: int, pass_prob: float):
    script_name = pick_operation()
    a, b = generate_inputs(script_name)
    correct = compute_correct_output(script_name, a, b)

    will_pass = random.random() < pass_prob
    if will_pass:
        output = correct
    else:
        output = generate_faulty_output(script_name, a, b, correct)

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
        case = random_case(idx, PROB_DIST)
        test_cases[case["id"]] = {
            "input": case["input"],
            "output": case["output"],
            "script": case["script"],
        }
    os.makedirs("test", exist_ok=True)
    cases_path = os.path.join("test", "test-cases.json")
    with open(cases_path, "w") as f:
        json.dump(test_cases, f, indent=2)
    print(f"Generated {NUM_TESTS} test cases with PASS_PROB={PROB_DIST}.")

if __name__ == "__main__":
    main()
