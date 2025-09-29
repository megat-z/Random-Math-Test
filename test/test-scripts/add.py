import json
import sys
from calculate import add

def run_test():
    with open("test/test-cases.json") as f:
        cases = json.load(f)
    status = True
    for cid, case in cases.items():
        a, b = case["input"]
        expected = case["output"]
        result = add(a, b)
        if result == expected:
            print(f"Pass: True | {cid}: {a}+{b}={result} == {expected}")
        else:
            print(f"Pass: False | {cid}: {a}+{b}={result} != {expected}")
            status = False
    print(f"Pass: {status}")

if __name__ == "__main__":
    run_test()
