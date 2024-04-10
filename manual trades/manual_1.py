max = 0

#print([x / 10.0 for x in range(0, 1000)])

for bid1 in range(100):
    for bid2 in range(bid1+1, 100):
        profit = 0
        for fish in [x / 10.0 for x in range(0, 1000)]:
            if fish >= bid2:
                profit += bid2
            elif fish >= bid1:
                profit += bid1

        if profit >= max:
            max = profit
            print(bid1, bid2, profit)