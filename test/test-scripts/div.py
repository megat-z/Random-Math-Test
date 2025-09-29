import sys
import math
from calculate import div

def test_division(input1, input2, expected):
    try:
        result = div(input1, input2)
        if isinstance(expected, str) and expected == "ZeroDivisionError":
            assert False, f"Expected ZeroDivisionError, but got {result}"
        if isinstance(result, float) or isinstance(expected, float):
            assert math.isclose(result, expected, rel_tol=1e-9), f"{result} != {expected}"
        else:
            assert result == expected, f"{result} != {expected}"
    except ZeroDivisionError:
        assert input2 == 0, "ZeroDivisionError raised but input2 is not zero"
        assert expected == "ZeroDivisionError", "ZeroDivisionError raised but not expected"

if __name__ == "__main__":
    input1 = int(sys.argv[1])
    input2 = int(sys.argv[2])
    arg3 = sys.argv[3]
    # Try to parse expected as float/int; if not, keep as string
    try:
        expected = float(arg3) if '.' in arg3 else int(arg3)
    except ValueError:
        expected = arg3
    test_division(input1, input2, expected)
