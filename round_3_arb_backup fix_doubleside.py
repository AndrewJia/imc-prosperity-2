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
    orchid_cache = []
    orchid_dim = 4

    orchid_import_cache = []
    orchid_sell_cache = []

    round3_caches = {'CHOCOLATE':[], 'STRAWBERRIES':[], 'ROSES':[], 'GIFT_BASKET':[]}
    position_limits = {'CHOCOLATE':250, 'STRAWBERRIES':350, 'ROSES':60, 'GIFT_BASKET':60}

    arb_target = 0
    gift_arb_pos = 0

    def calc_next_price_starfruit(self):
        # starfruit cache stores price from 1 day ago, current day resp
        # by price, here we mean mid price

        ## dim 4 coef
        coef = [0.8090892, 0.16316049, 0.0455032, -0.01869561]
        intercept = 4.481696494462085

        ## dim 6 coef
        #coef = [0.31088816, 0.22427233, 0.14790473, 0.12669606, 0.09051234, 0.09689353]
        #intercept = 14.33334143594766
        nxt_price = intercept
        for i, val in enumerate(self.starfruit_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    def calc_next_price_orchid(self):
        coef = [.35, .3, .2, .15]
        intercept = 0
        nxt_price = intercept
        for i, val in enumerate(self.orchid_cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    def calc_weighted(self, cache):
        coef = [.35, .3, .2, .15]
        nxt_price = 0
        for i, val in enumerate(cache):
            nxt_price += val * coef[i]

        return int(round(nxt_price))
    
    def calc_weighted_dim(self, cache, dim=6):
        if dim == 4:
            coef = [.35, .3, .2, .15]
        elif dim == 6:
            coef = [.3, .2, .15, .15, .1, .1]
        else:
            logger.print("wrong dimensions!")
            return cache[0]
        
        nxt_price = 0
        for i, val in enumerate(cache):
            nxt_price += val * coef[i]
        return int(round(nxt_price))
    
    def round3(self, product, order_depth, orders, state, taking, making):
        #price calculation
        curr_cache = self.round3_caches[product]
        w_price = self.calc_weighted_dim(curr_cache)
        #logger.print(product, " priced at ", w_price)

        #get position data
        max_position = self.position_limits[product]
        if product in state.position:
            current_position = state.position[product]
        else:
            state.position[product] = 0
            current_position = 0
        
        acceptable_price_buy = w_price - 2
        acceptable_price_sell = w_price + 2
        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

        buy_dep = len(order_depth.buy_orders)
        sell_dep = len(order_depth.sell_orders)

        sec_ask = best_ask + 4  # idk these, might change later
        sec_bid = best_bid - 4
        if sell_dep >= 2:
            sec_ask, _ = list(order_depth.sell_orders.items())[1]
        if buy_dep >= 2:
            sec_bid, _ = list(order_depth.buy_orders.items())[1]

        #cache logic
        cache_len = len(curr_cache)
        if cache_len == 6:   # if at max len, pop last (right)
            curr_cache.pop(-1)
        curr_cache.insert(0, (best_ask+best_bid)/2) # always insert to left
                # if we don't got full cache, no market taking
        if cache_len == 6 and taking:          
            if int(best_ask) <= acceptable_price_buy:
                #logger.print("BUY", product, min(20-current_position, -best_ask_amount), "x", best_ask)
                orders.append(Order(product, best_ask, min(max_position-current_position, -best_ask_amount)))
                current_position += min(max_position-current_position, -best_ask_amount)

            if int(best_bid) >= acceptable_price_sell:
                #logger.print("SELL", product, max(-20-current_position, -best_bid_amount), "x", best_bid)
                orders.append(Order(product, best_bid, max(-max_position-current_position, -best_bid_amount)))
                current_position += max(-max_position-current_position, -best_bid_amount)


        
        # MARKET MAKING
        if making == False: return

        #w_price = self.calc_weighted_dim(curr_cache)
        max_sell_amt = min(max_position+current_position, max_position+state.position[product])
        max_buy_amt = min(max_position-current_position, max_position-state.position[product])
        spread = best_ask - best_bid

        if spread > 8: return
        
        # undercut second sell
        if best_ask <= w_price or current_position <= -max_position/2:
            under_ask = sec_ask - 1
            orders.append(Order(product, under_ask, round(-max_sell_amt/3)))
        # undercut best sell
        else:
            #logger.print("undercut best sell")
            under_ask = best_ask - 1
            orders.append(Order(product, under_ask, round(-max_sell_amt/3)))

        # undercut second buy
        if best_bid >= w_price or current_position >= max_position/2:
            under_bid = sec_bid + 1
            orders.append(Order(product, under_bid, round(max_buy_amt/3)))
        # undercut best buy
        else:
            #logger.print("undercut best buy")
            under_bid = best_bid + 1
            orders.append(Order(product, under_bid, round(max_buy_amt/3))) 

    def round3_arbitrage(self, state, result):
        mvg_const = 0.5     # arbitrage target position moving average const
        max_exposure = (58.333/60.0)  # target max exposure for arbitrage (at +/- max_range from mean)
        buffer = 60         # how much spread we do nothing on (due to cost of buying/selling)
        max_range = 90     # what value of spread leads to max exposure

        sum_price = 4 * self.round3_caches['CHOCOLATE'][0] + 6 * self.round3_caches['STRAWBERRIES'][0] + self.round3_caches['ROSES'][0]
        gift_price = self.round3_caches['GIFT_BASKET'][0]
        logger.print(self.round3_caches['CHOCOLATE'][0], self.round3_caches['STRAWBERRIES'][0], self.round3_caches['ROSES'][0])
        logger.print('gift price ', gift_price, ' sum price ', sum_price)
        norm_spread =  gift_price - sum_price - 380
        logger.print("norm_spread: ", norm_spread)

        
        if abs(norm_spread) < buffer:
            curr_target = 0
        else:
            if norm_spread > 0:
                curr_target = (60 * max_exposure) * (norm_spread - buffer) / (max_range - buffer)
                curr_target = min(curr_target, 60*max_exposure) #limit curr_target to +/- 60
            else:
                curr_target = (60 * max_exposure) * (norm_spread + buffer) / (max_range - buffer)
                curr_target = max(curr_target, -60*max_exposure)

        if self.arb_target > 0:
            self.arb_target = max(self.arb_target, curr_target)
            if norm_spread < -buffer:
                self.arb_target = 0
        elif self.arb_target < 0:
            self.arb_target = min(self.arb_target, curr_target)
            if norm_spread > buffer:
                self.arb_target = 0
        else:
            self.arb_target = curr_target

        logger.print("curr_target: ", curr_target, "arb_target: ", self.arb_target)

        self.round3_arb_order(state, state.order_depths['CHOCOLATE'], 'CHOCOLATE', 4, result)
        self.round3_arb_order(state, state.order_depths['STRAWBERRIES'], 'STRAWBERRIES', 6, result)
        self.round3_arb_order(state, state.order_depths['ROSES'], 'ROSES', 1, result)
        self.round3_arb_order(state, state.order_depths['GIFT_BASKET'], 'GIFT_BASKET', -1, result)
    
    def round3_arb_order(self, state, order_depth, product, count_in_basket, result):
        if product in state.position:
            current_position = state.position[product]
        else:
            current_position = 0

        if product == 'GIFT_BASKET': current_position = self.gift_arb_pos

        target_position = round(self.arb_target * count_in_basket)

        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

        # we gotta buy
        if current_position < target_position: 
            buying_amt = min(target_position - current_position, abs(best_ask_amount))
            result[product].append(Order(product, best_ask, buying_amt))
            if product == 'GIFT_BASKET': self.gift_arb_pos += buying_amt
        # we gotta sell
        elif current_position > target_position:
            selling_amt = min(abs(target_position - current_position), abs(best_bid_amount))
            result[product].append(Order(product, best_bid, -selling_amt))
            if product == 'GIFT_BASKET': self.gift_arb_pos -= selling_amt


        

    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        #print("traderData: " + state.traderData)
        #print("Observations: " + str(state.observations))
        #print(state.position)
        conversions = 0
        result = {'GIFT_BASKET':[], 'CHOCOLATE':[], 'STRAWBERRIES':[], 'ROSES':[], 'GIFT_BASKET':[], 'STARFRUIT':[], 'AMETHYSTS':[], 'ORCHIDS':[]}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            buy_dep = len(order_depth.buy_orders)
            sell_dep = len(order_depth.sell_orders)
            
            #logger.print("Buy Order depth : " + str(buy_dep) + ", Sell order depth : " + str(sell_dep))

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
                    #logger.print("BUY", product, min(20-current_position, -best_ask_amount), "x", best_ask)
                    orders.append(Order(product, best_ask, min(20-current_position, -best_ask_amount)))
                    current_position += min(20-current_position, -best_ask_amount)

                if int(best_bid) >= acceptable_price_sell:
                    #logger.print("SELL", product, max(-20-current_position, -best_bid_amount), "x", best_bid)
                    orders.append(Order(product, best_bid, max(-20-current_position, -best_bid_amount)))
                    current_position += max(-20-current_position, -best_bid_amount)

                #logger.print("position before market making is ", current_position, state.position[product])
                
                # MARKET MAKING

                max_sell_amt = min(20+current_position, 20+state.position[product])
                max_buy_amt = min(20-current_position, 20-state.position[product])

                # reset position using 10000s
                if best_ask == 10000 and current_position < 0:
                    canbuy = min(abs(current_position), abs(best_ask_amount))
                    orders.append(Order(product, 10000, canbuy))
                    max_buy_amt -= canbuy
                if best_bid == 10000 and current_position > 0:
                    cansell = min(abs(current_position), abs(best_bid_amount))
                    orders.append(Order(product, 10000, -cansell))
                    max_sell_amt -= cansell
                
                
                # undercut second
                if best_ask <= 10000 or current_position <= -10:
                    under_ask = sec_ask - 1
                    #if current_position <= -5:
                    #    under_ask = max(10000, under_ask - 1)
                    orders.append(Order(product, under_ask, -max_sell_amt))
                # undercut best
                else:
                    #logger.print("undercut best sell")
                    under_ask = best_ask - 1
                    # try reset position
                    if current_position >= 18:
                        orders.append(Order(product, max(10000, under_ask - 2), -5))
                        max_sell_amt -= 5
                        under_ask = max(10000, under_ask - 1)
                    elif current_position >= 10:
                        under_ask = max(10000, under_ask - 1)
                    orders.append(Order(product, under_ask, -max_sell_amt))

                # can't undercut best
                if best_bid >= 10000 or current_position >= 10:
                    under_bid = sec_bid + 1
                    #if current_position <= -5:
                    #    under_bid = min(10000, under_bid + 1)
                    orders.append(Order(product, under_bid, max_buy_amt))
                # can undercut best
                else:
                    #logger.print("undercut best buy")
                    under_bid = best_bid + 1
                    # try reset position
                    if current_position <= -18:
                        orders.append(Order(product, min(10000, under_bid + 2), 5))
                        max_buy_amt -= 5
                        under_bid = min(10000, under_bid + 1)
                    elif current_position <= -10:
                        under_bid = min(10000, under_bid + 1)
                    orders.append(Order(product, under_bid, max_buy_amt))

            elif product == 'STARFRUIT':
                s_price = self.calc_next_price_starfruit()
                #logger.print(self.starfruit_cache, "STARFRUIT PRICED AT ", s_price)
                acceptable_price_buy = s_price - 1
                acceptable_price_sell = s_price + 1

                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

                sec_ask = best_ask + 4  # idk these, might change later
                sec_bid = best_bid - 4

                if sell_dep >= 2:
                    sec_ask, _ = list(order_depth.sell_orders.items())[1]
                if buy_dep >= 2:
                    sec_bid, _ = list(order_depth.buy_orders.items())[1]

                #starfruit cache logic
                starfruit_len = len(self.starfruit_cache)
                if len(self.starfruit_cache) == self.starfruit_dim:   # if at max len, pop last (right)
                    self.starfruit_cache.pop(-1)
                self.starfruit_cache.insert(0, (best_ask+best_bid)/2) # always insert to left
                        # if we don't got full cache, no market taking
                if starfruit_len == self.starfruit_dim:          
                    if round(best_ask) <= acceptable_price_buy:
                        #logger.print("BUY", product, min(20-current_position, -best_ask_amount), "x", best_ask)
                        orders.append(Order(product, best_ask, min(20-current_position, -best_ask_amount)))
                        current_position += min(20-current_position, -best_ask_amount)

                    if round(best_bid) >= acceptable_price_sell:
                        #logger.print("SELL", product, max(-20-current_position, -best_bid_amount), "x", best_bid)
                        orders.append(Order(product, best_bid, max(-20-current_position, -best_bid_amount)))
                        current_position += max(-20-current_position, -best_bid_amount)


                
                # MARKET MAKING
                max_sell_amt = min(20+current_position, 20+state.position[product])
                max_buy_amt = min(20-current_position, 20-state.position[product])
                
                
                # undercut second
                if best_ask <= s_price or current_position <= -10:
                    under_ask = sec_ask - 1
                    #if current_position <= -5:
                    #    under_ask = max(10000, under_ask - 1)
                    orders.append(Order(product, under_ask, -max_sell_amt))
                # undercut best
                else:
                    #logger.print("undercut best sell")
                    under_ask = best_ask - 1
                    # try reset position
                    '''
                    if current_position >= 18:
                        orders.append(Order(product, max(s_price-1, under_ask - 2), -5))
                        max_sell_amt -= 5
                        under_ask = max(s_price-1, under_ask - 1)
                    #elif current_position >= 10:
                    #    under_ask = max(s_price, under_ask - 1)  '''
                    orders.append(Order(product, under_ask, -max_sell_amt))

                # can't undercut best
                if best_bid >= s_price or current_position >= 10:
                    under_bid = sec_bid + 1
                    #if current_position <= -5:
                    #    under_bid = min(10000, under_bid + 1)
                    orders.append(Order(product, under_bid, max_buy_amt))
                # can undercut best
                else:
                    #logger.print("undercut best buy")
                    under_bid = best_bid + 1
                    '''
                    # try reset position
                    if current_position <= -18:
                        orders.append(Order(product, min(s_price+1, under_bid + 2), 5))
                        max_buy_amt -= 5
                        under_bid = min(s_price+1, under_bid + 1)
                    #elif current_position <= -10:
                    #    under_bid = min(s_price, under_bid + 1) '''
                    orders.append(Order(product, under_bid, max_buy_amt)) 
            
            elif product == 'ORCHIDS':
                s_price = self.calc_next_price_orchid()
                #logger.print(self.orchid_cache, "ORCHID PRICED AT ", s_price)
                #acceptable_price_buy = s_price - 1
                #acceptable_price_sell = s_price + 1

                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]


                # conversions
                #orchid_obs = state.observations.conversionObservations['ORCHIDS']
                #logger.print(orchid_obs)
                conversion_observations = {}
                for product, observation in state.observations.conversionObservations.items():
                    conversion_observations[product] = [
                        observation.bidPrice,
                        observation.askPrice,
                        observation.transportFees,
                        observation.exportTariff,
                        observation.importTariff,
                        observation.sunlight,
                        observation.humidity,
                    ]
                
                obs_ask_price = conversion_observations['ORCHIDS'][1]
                obs_trans_fee = conversion_observations['ORCHIDS'][2]
                obs_imp_tariff = conversion_observations['ORCHIDS'][4]
                
                orchid_importtotalPrice = (obs_ask_price + obs_trans_fee + obs_imp_tariff)
                logger.print(orchid_importtotalPrice)

                #orchid cache logic
                orchid_len = len(self.orchid_import_cache)
                if len(self.orchid_import_cache) == self.orchid_dim:   # if at max len, pop last (right)
                    self.orchid_import_cache.pop(-1)
                    self.orchid_sell_cache.pop(-1)
                self.orchid_import_cache.insert(0, orchid_importtotalPrice) # always insert to left
                self.orchid_sell_cache.insert(0, best_bid)
                    #if not full cache gtfo
                if orchid_len < self.orchid_dim:
                    conversions = 0
                    continue

                # weighted avg here
                # sell first
                #logger.print('sell prices', self.orchid_sell_cache, self.calc_weighted(self.orchid_sell_cache))
                #logger.print('import prices', self.orchid_import_cache, self.calc_weighted(self.orchid_import_cache))
                
                if best_bid > self.calc_weighted(self.orchid_import_cache):
                    orders.append(Order(product, best_bid, -best_bid_amount))
                
                if orchid_importtotalPrice < self.calc_weighted(self.orchid_sell_cache):
                    conversions = -current_position
                else:
                    conversions = 0
                    
            
            #round 3
            elif product in ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']:
                if product == 'GIFT_BASKET':
                    #logger.print("running gift baskets")
                    self.round3(product, order_depth, orders, state, False, making=False)
                else:
                    #logger.print("running ", product)
                    self.round3(product, order_depth, orders, state, False, False)
            
            result[product] = orders
        self.round3_arbitrage(state, result)
    

        traderData = "GABAGOOL" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData