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
    starfruit_dim = 4 #6

    #robbery
    def calc_next_price_starfruit(self):
        # starfruit cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        ## dim 4 coef
        coef = [-0.01869561,  0.0455032 ,  0.16316049,  0.8090892]
        intercept = 4.481696494462085

        ## dim 6 coef
        #coef = [0.31088816, 0.22427233, 0.14790473, 0.12669606, 0.09051234, 0.09689353]
        #intercept = 14.33334143594766
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
            
            buy_dep = len(order_depth.buy_orders)
            sell_dep = len(order_depth.sell_orders)
            
            logger.print("Buy Order depth : " + str(buy_dep) + ", Sell order depth : " + str(sell_dep))

            if product in state.position:
                current_position = state.position[product]
            else:
                state.position[product] = 0
                current_position = 0

            if product == 'AMETHYSTS':
                
                acceptable_price_buy = 9998
                acceptable_price_sell = 10002
                
                # if price is good, buy all that we can
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                # get 2nd best ask_bid
                sec_ask = 10005
                sec_bid = 9995
                if sell_dep >= 2:
                    sec_ask, _ = list(order_depth.sell_orders.items())[1]
                if buy_dep >= 2:
                    sec_bid, _ = list(order_depth.buy_orders.items())[1]

                if int(best_ask) <= acceptable_price_buy:
                    logger.print("BUY", product, min(20-current_position, -best_ask_amount), "x", best_ask)
                    orders.append(Order(product, best_ask, min(20-current_position, -best_ask_amount)))
                    current_position += min(20-current_position, -best_ask_amount)

                if int(best_bid) >= acceptable_price_sell:
                    logger.print("SELL", product, max(-20-current_position, -best_bid_amount), "x", best_bid)
                    orders.append(Order(product, best_bid, max(-20-current_position, -best_bid_amount)))
                    current_position += max(-20-current_position, -best_bid_amount)

                logger.print("position before market making is ", current_position, state.position[product])
                
                # reset position
                #orders.append(Order(product, 10000, -current_position))
                
                # MARKET MAKING
                # if best ask/bid cannot be undercut we take it
                # -> undercut 2nd best; if no 2nd best, take the +/- 5 positions
                # if |position| > 15, undercut 2nd best; if no 2nd best, take the +/- 5 position
                # if |position| > 8, ignore best price if its quantity is 1 or 2 and undercut 2nd
                max_sell_amt = min(20+current_position, 20+state.position[product])
                max_buy_amt = min(20-current_position, 20-state.position[product])
                
                # undercut second
                if best_ask <= 10000 or current_position <= -15       \
                or (current_position <= -8 and best_ask_amount <= 2)  \
                or (current_position <= -5 and best_ask_amount <= 1):
                    under_ask = sec_ask - 1
                    orders.append(Order(product, under_ask, -max_sell_amt))
                # undercut best
                else:
                    under_ask = best_ask - 1
                    if current_position <= -15:
                        under_ask = max(10000, under_ask - 2)
                    if current_position <= -10:
                        under_ask = max(10000, under_ask - 1)
                    orders.append(Order(product, under_ask, -max_sell_amt))

                # can't undercut best
                if best_bid >= 10000 or current_position >= 15        \
                or (current_position >= 8 and best_ask_amount <= 2)   \
                or (current_position >= 5 and best_ask_amount <= 1):
                    under_bid = sec_bid + 1
                    orders.append(Order(product, under_bid, max_buy_amt))
                # can undercut best
                else:
                    under_bid = best_bid + 1
                    if current_position >= 15:
                        under_bid = min(10000, under_bid + 2)
                    elif current_position >= 10:
                        under_bid = min(10000, under_bid + 1)
                    orders.append(Order(product, under_bid, max_buy_amt))

                
            else:
                break
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