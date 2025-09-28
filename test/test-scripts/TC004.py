# Auto-generated test script for TC004
a = 42
b = 29
result = a - b
expected = 13
print('Input:', a, '-', b)
print('Expected Output:', expected)
print('Actual Output:', result)
print('Pass:', abs(result - float(expected)) < 1e-9)
