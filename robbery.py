from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string


class Trader:

    #robbery
    def calc_next_price_bananas(self):
        # bananas cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [-0.01869561,  0.0455032 ,  0.16316049,  0.8090892]
        intercept = 4.481696494462085
        nxt_price = intercept
        for i, val in enumerate(self.bananas_cache):
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
                acceptable_price_buy = 10
                acceptable_price_sell = 10
                continue #skip starfruit for now

            
            for (ask_price, ask_amount) in list(order_depth.sell_orders.items()):
                if int(ask_price) <= acceptable_price_buy:
                    print("BUY", str(-ask_amount) + "x", ask_price)
                    #orders.append(Order(product, ask_price, -ask_amount))
                    orders.append(Order(product, ask_price, 20-current_position))

            for (bid_price, bid_amount) in list(order_depth.buy_orders.items()):
                if int(bid_price) >= acceptable_price_sell:
                    print("SELL", str(bid_amount) + "x", bid_price)
                    #orders.append(Order(product, bid_price, -bid_amount))
                    orders.append(Order(product, bid_price, -20-current_position))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData