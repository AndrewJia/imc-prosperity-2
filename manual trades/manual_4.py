max_profit = 0
best_bid_low = 0

#print([x / 10.0 for x in range(0, 1000)])
for bid_high in range(902, 1000, 1):
    max_profit = best_bid_low = 0
    for bid_low in range(901, bid_high, 1):
        profit = 0

        for fish in [x / 10.0 for x in range(9000, 10000)]: #high-tech fish generator
            fishfactor = (fish - 900.0) / 100.0 #triangular distribution xdd
            
            if bid_low >= fish:
                profit += (1000 - bid_low) * fishfactor
            elif bid_high >= fish:
                profit += (1000 - bid_high) * fishfactor
            else:
                pass #womp womp

        if profit >= max_profit:
            max_profit = profit
            best_bid_low = bid_low
            #print(bid_low, bid_high, profit)
    
    print('best low bid for high', bid_high, 'is', best_bid_low,'profit = ', max_profit)
    