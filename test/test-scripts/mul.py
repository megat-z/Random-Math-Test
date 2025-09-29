import sys
import math
from calculate import mul

def test_case(input1, input2, expected):
    result = mul(input1, input2)
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9), f"{result} != {expected}"
    else:
        assert result == expected, f"{result} != {expected}"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python mul.py <input1> <input2> <expected>")
        sys.exit(1)
    input1 = float(sys.argv[1]) if '.' in sys.argv[1] else int(sys.argv[1])
    input2 = float(sys.argv[2]) if '.' in sys.argv[2] else int(sys.argv[2])
    expected = float(sys.argv[3]) if '.' in sys.argv[3] else int(sys.argv[3])
    test_case(input1, input2, expected)
