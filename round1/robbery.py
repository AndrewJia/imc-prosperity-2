from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import string
import json

import collections
from collections import defaultdict

## logger class for JMerle's visualizer
class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        print(json.dumps([
            self.compress_state(state),
            self.compress_orders(orders),
            conversions,
            trader_data,
            self.logs,
        ], cls=ProsperityEncoder, separators=(",", ":")))

        self.logs = ""

    def compress_state(self, state: TradingState) -> list[Any]:
        return [
            state.timestamp,
            state.traderData,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

logger = Logger()


class Trader:

    starfruit_cache = []
    starfruit_dim = 6

    #robbery
    def calc_next_price_starfruit(self):
        # starfruit cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        coef = [0.31088816, 0.22427233, 0.14790473, 0.12669606, 0.09051234,
       0.09689353]
        intercept = 14.33334143594766
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        #print("traderData: " + state.traderData)
        #print("Observations: " + str(state.observations))
        #print(state.position)
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            
            logger.print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))

            if product in state.position:
                current_position = state.position[product]
            else:
                current_position = 0

            if product == 'AMETHYSTS':
                acceptable_price_buy = 9999
                acceptable_price_sell = 10001
                
                '''if current_position <= -5:
                    acceptable_price_buy = 10000
                if current_position >= 5:
                    acceptable_price_sell = 10000'''

                # if price is good, buy all that we can
                # if resetting position (price=10000) buy until we hit 0
                for (ask_price, ask_amount) in list(order_depth.sell_orders.items()):
                    if int(ask_price) <= acceptable_price_buy:
                        #logger.print("BUY", product, str(-ask_amount) + "x", ask_price)
                        #orders.append(Order(product, ask_price, -ask_amount))
                        logger.print("BUY", product, str(-ask_amount) + "x", min(20-current_position, -ask_amount))
                        orders.append(Order(product, ask_price, min(20-current_position, -ask_amount)))
                        current_position += min(20-current_position, -ask_amount)

                for (bid_price, bid_amount) in list(order_depth.buy_orders.items()):
                    if int(bid_price) >= acceptable_price_sell:
                        #logger.print("SELL", product, str(bid_amount) + "x", bid_price)
                        #orders.append(Order(product, bid_price, -bid_amount))
                        logger.print("SELL", product, str(bid_amount) + "x", max(-20-current_position, -bid_amount))
                        orders.append(Order(product, bid_price, max(-20-current_position, -bid_amount)))
                        current_position += max(-20-current_position, -bid_amount)
                
                # reset position
                orders.append(Order(product, 10000, -current_position))

                
            else:
                s_price = self.calc_next_price_starfruit()
                logger.print(self.starfruit_cache, "STARFRUIT PRICED AT ", s_price)
                acceptable_price_buy = s_price - 1
                acceptable_price_sell = s_price + 1

                

                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                starfruit_len = len(self.starfruit_cache)
                
                if len(self.starfruit_cache) == self.starfruit_dim:
                    self.starfruit_cache.pop(-1)
                
                self.starfruit_cache.insert(0, (best_ask+best_bid)/2)

                if starfruit_len < self.starfruit_dim:
                    logger.print(len(self.starfruit_cache))
                    continue


                for (ask_price, ask_amount) in list(order_depth.sell_orders.items()):
                    if int(ask_price) <= acceptable_price_buy:
                        #logger.print("BUY", product, str(-ask_amount) + "x", ask_price)
                        #orders.append(Order(product, ask_price, -ask_amount))
                        logger.print("BUY", product, str(-ask_amount) + "x", 20-current_position)
                        orders.append(Order(product, ask_price, 20-current_position))
                        break

                for (bid_price, bid_amount) in list(order_depth.buy_orders.items()):
                    if int(bid_price) >= acceptable_price_sell:
                        #logger.print("SELL", product, str(bid_amount) + "x", bid_price)
                        #orders.append(Order(product, bid_price, -bid_amount))
                        logger.print("SELL", product, str(bid_amount) + "x", -20-current_position)
                        orders.append(Order(product, bid_price, -20-current_position))
                        break
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 0
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData