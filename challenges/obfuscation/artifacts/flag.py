flag = input("flag: ")

flag = ''.join([str(ord(flag[i])-15) for i in range(len(flag))])

if flag == '8793828810810010482658580104348780100349483339375110':
    print("Correct!")
else:
    print("Incorrect!")