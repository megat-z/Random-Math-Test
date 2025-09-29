import sys
import math
from calculate import add

def test_addition(input1, input2, expected):
    result = add(input1, input2)
    assert result == expected, f"{result} != {expected}"

if __name__ == "__main__":
    input1 = int(sys.argv[1])
    input2 = int(sys.argv[2])
    expected = int(sys.argv[3])
    test_addition(input1, input2, expected)
