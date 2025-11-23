flag = input("flag: ")

result = []

while len(flag) > 0:
    indices = set()
    for i in range(0, len(flag), 3):
        indices.add(i)
        result.append(flag[i])
    flag = ''.join([c for idx, c in enumerate(flag) if idx not in indices])

result = ''.join(result)

if result == 'fgtcn3zlXt_}a@r{gr1d':
    print("Correct!")
else:
    print("Incorrect!")