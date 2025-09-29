import sys
import math
from calculate import mul

def test_multiplication(input1, input2, expected):
    result = mul(input1, input2)
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9), f"{result} != {expected}"
    else:
        assert result == expected, f"{result} != {expected}"

if __name__ == "__main__":
    input1 = int(sys.argv[1])
    input2 = int(sys.argv[2])
    expected = float(sys.argv[3]) if '.' in sys.argv[3] else int(sys.argv[3])
    test_multiplication(input1, input2, expected)
