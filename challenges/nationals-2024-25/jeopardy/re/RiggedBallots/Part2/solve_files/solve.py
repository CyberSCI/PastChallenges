order = [3, 36, 10, 1, 5, 22, 26, 30, 31, 21, 7, 12, 33, 23, 14, 29, 28, 2, 25, 27, 20, 9, 24, 0, 35, 4, 19, 16, 8, 15, 6, 32, 17, 13, 18, 11, 34]
reorder_FLAG = []

with open('Ballots.txt', 'r') as file:
    FLAG = file.readlines()

flag_single = list(set(FLAG))
#print(len(flag_single))
for name in flag_single:   
    reorder = []
    for i in range(0, 37):
        index = order.index(i)
        try:
            reorder.append(name[index])
        except:
            print(name)
            print(FLAG.index(name))
    print("".join(reorder[::-1]))
    reorder_FLAG.append("".join(reorder[::-1]))

Start = "CybersciNats"
found = 1

for name in reorder_FLAG:
    Checker =  name[:12]
    for i in range(0,100):
        finder_flag = []
        for letter in Start:
            new_letter = ord(letter)
            if (new_letter+i)<126:
                new_letter = new_letter+i
            try:
                finder_flag.append(chr(int(new_letter)))
            except:
                break
        finder_flag = "".join(finder_flag)
        if Checker == finder_flag:
            change = i
            print(change)
