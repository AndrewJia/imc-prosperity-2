for hypothetical_avg in range(978, 1000):
    max_profit = best_low = best_high = 0

    for bid_low in range(951, 1000, 1):
        for bid_high in range(bid_low + 1, 1000, 1):
            profit = 0

            for fish in [x / 10.0 for x in range(9000, 10000)]: #high-tech fish generator
                fishfactor = (fish - 900.0) / 100.0 #triangular distribution xdd
                manfactor = (1000.0 - hypothetical_avg) / (1000.0 - bid_high) 
                manfactor = min(1.0, manfactor)
                
                if bid_low >= fish:
                    profit += (1000 - bid_low) * fishfactor
                elif bid_high >= fish:
                    profit += (1000 - bid_high) * fishfactor * manfactor
                else:
                    pass #womp womp

            if profit >= max_profit:
                max_profit = profit
                best_low = bid_low
                best_high = bid_high
    
    print('best bids for average', hypothetical_avg, 'is', best_low, best_high, max_profit)
    