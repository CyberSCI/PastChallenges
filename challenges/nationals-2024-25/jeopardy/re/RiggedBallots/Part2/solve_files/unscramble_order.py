line_counts = []
i = 0

with open('Ballots.txt', 'r') as file:
    ballots = file.readlines()

length = len(ballots)
count = 0
check = ballots[0]
for line in ballots:
    if check.strip() == line.strip():
        i = i + 1
    else:
        if i == 1 and "This" in check:
            i = 0
        check = line.strip()
        line_counts.append(i)
        i = 1

    count = count + 1
    if check == ballots[-1] and count == length:
        line_counts.append(i)
    

print(line_counts)
