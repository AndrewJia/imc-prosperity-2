from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

import collections
from collections import defaultdict


class Trader:

    starfruit_cache = []
    starfruit_dim = 4

    #robbery
    def calc_next_price_starfruit(self):
        # starfruit cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [-0.01869561,  0.0455032 ,  0.16316049,  0.8090892]
        intercept = 4.481696494462085
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        #print("traderData: " + state.traderData)
        #print("Observations: " + str(state.observations))
        print(state.position)
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))

            if product in state.position:
                current_position = state.position[product]
            else:
                current_position = 0

            if product == 'AMETHYSTS':
                acceptable_price_buy = 9999
                acceptable_price_sell = 10001
                
                if current_position <= -15:
                    acceptable_price_buy = 10000
                if current_position >= 15:
                    acceptable_price_sell = 10000
                
            else:
                if len(self.starfruit_cache) == self.starfruit_dim:
                    self.starfruit_cache.pop(0)

                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                self.starfruit_cache.append((best_ask+best_bid)/2)

                s_price = self.calc_next_price_starfruit()
                print("STARFRUIT PRICED AT ", s_price)
                acceptable_price_buy = s_price - 1
                acceptable_price_sell = s_price + 1

            
            for (ask_price, ask_amount) in list(order_depth.sell_orders.items()):
                if int(ask_price) <= acceptable_price_buy:
                    print("BUY", product, str(-ask_amount) + "x", ask_price)
                    #orders.append(Order(product, ask_price, -ask_amount))
                    orders.append(Order(product, ask_price, 20-current_position))
                    break

            for (bid_price, bid_amount) in list(order_depth.buy_orders.items()):
                if int(bid_price) >= acceptable_price_sell:
                    print("SELL", product, str(bid_amount) + "x", bid_price)
                    #orders.append(Order(product, bid_price, -bid_amount))
                    orders.append(Order(product, bid_price, -20-current_position))
                    break
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData