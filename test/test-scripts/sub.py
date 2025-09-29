import sys
import math
from calculate import sub

def test_subtraction(input1, input2, expected):
    result = sub(input1, input2)
    assert result == expected, f"{result} != {expected}"

if __name__ == "__main__":
    input1 = int(sys.argv[1])
    input2 = int(sys.argv[2])
    expected = int(sys.argv[3])
    test_subtraction(input1, input2, expected)
