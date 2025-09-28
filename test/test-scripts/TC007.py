# Auto-generated test script for TC007
a = 1
b = 100
result = a / b
expected = 0.01
print('Input:', a, '/', b)
print('Expected Output:', expected)
print('Actual Output:', result)
print('Pass:', abs(result - float(expected)) < 1e-9)
