import pandas as pd
import numpy as np
from glob import glob
import time
from datetime import datetime

import ccxt
import ta

from data_provider import market_to_symbol
pd.set_option('precision', 9)

main_key = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"

tf_dict = {'1m':60, '3m':180, '5m':300, '15m':1500, '30m': 3000, '1h':6000}
balance_assets = ['USDT','BTC','BNB']

api_key = main_key
api_secret = main_secret

exchange = ccxt.binance({'apiKey': api_key,
                         'secret': api_secret})


#--------------------Robot---------------------------------------------------

def create_market_buy_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_buy_order(symbol, amount)
    trades = exchange.fetchMyTrades(symbol, limit = 1)
    price = trades[-1]['price']
    return price

def create_market_sell_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_sell_order(symbol, amount)
    trades = exchange.fetchMyTrades(symbol, limit = 1)
    price = trades[-1]['price']
    return price

def current_bid_ask(exchange, symbol):
    orderbook = exchange.fetch_order_book (symbol)
    bid = orderbook['bids'][0][0] if len (orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len (orderbook['asks']) > 0 else None
    return (bid, ask)    

def average_ob_price(bid, ask):
    return round((bid + ask)/2, 2)

def get_balance():
    json = exchange.fetch_balance()
    df = pd.DataFrame(json['info']['balances'])
    return df

def get_balance_values(df, assets):
    if type(assets) == list :
        if len(assets) > 0:
            df = df[df['asset'].isin(assets)]
            df = df.set_index('asset').loc[assets].reset_index()
            res = df['free'].values.astype(float).tolist()
        else:
            res = []
    elif type(assets) == str :
        res = df[df['asset'] == assets]['free'].values.astype(float)[0]
    else:
        res = None
    return res

def format_results(col, vals):
    xx = zip(col, vals)
    res = []
    for col, val in xx:
        if type(val) == str:
            fr = '%s'
        elif type(val) == int:
            fr = '%d'
        elif type(val) == float:
            if abs(val) < 50:
                fr = '%2.3f'
            else:
                fr = '%5.2f'
        res.append(col + ': ' + fr)
    res = ', '.join(res)
    return res


from threading import Thread
import time
import abc
import logging
import os

import pandas as pd
from collections import namedtuple
Verbose = namedtuple('Verbose', ['mute', 'trades', 'full'])

class TradingSystem(abc.ABC):

    @abc.abstractclassmethod
    def absractloop(self):
        pass

    def mainloop(self):
        while(self._running):
            self.absractloop()
            
            #time.sleep(5)
            time.sleep(self.timeframe)
        print('Stop trading:',  datetime.now())
        print(self.market, self.tf, self.contract, self.robot.robot_name)

    def __init__(self, market, timeframe):
        self._running = True
        self.timeframe = timeframe
        self.market = market
        self.market_position = 0
        self.num_shares  = 0
        self.open_position = 0
        self.trade_profit = 0
        self.cum_profit = 0
        self.trades = 0
        self.commission = commission
        self.stop = False

        t = Thread(target=self.mainloop)
        t.start()
        print(self.market, self.tf, self.contract, self.robot.robot_name)
        print('Start trading:',  datetime.now(), )

        
    def terminate(self): 
        self._running = False
        
    def buy(self, contract, price):
        self.market_position = 1
        self.num_shares = self.num_shares + contract
        self.open_position = self.num_shares * price * (1 + self.commission)
        
    def sell(self, price):
        self.market_position = 0
        close_position = self.num_shares * price * (1-self.commission)
        self.trade_profit = close_position - self.open_position
        self.cum_profit   += self.trade_profit
        self.trades       +=  1
        self.num_shares    = 0
        self.open_position = 0       

    def trade_statistics(self, bid, ask, price_buy, price_sell):
        base_func = self.robot.func(self.prices)   
        base_func_names  = [x for i, x in enumerate(base_func) if i%2 == 0]
        base_func_values = [x for i, x in enumerate(base_func) if i%2 == 1]
        trade_time = exchange.milliseconds()
        df_balance = get_balance()
        balance = get_balance_values(df_balance, balance_assets)
        columns = ['T', 'bid', 'ask', 'price_buy', 'price_sell', 'MP']+ base_func_names  + ['num_shares', 'profit', 'cum_profit'] + balance_assets
        res = [trade_time, bid, ask, price_buy, price_sell, self.market_position] + base_func_values + [self.num_shares, self.trade_profit, self.cum_profit] + balance    
        if os.path.exists(self.stat_fn):
            df_res = pd.read_csv(self.stat_fn) 
        else:
            df_res = pd.DataFrame(columns = columns) 
        df_res = df_res.append(pd.DataFrame([dict(zip(columns, res))]))
        df_res.to_csv(self.stat_fn, index = False)

        if self.verbose == Verbose.full or self.verbose == Verbose.trades and (price_sell or price_buy):
            trade_time = datetime.fromtimestamp(res[0]/1000).strftime('%H:%M:%S')
            res_tuple  = tuple([trade_time] + res[1:-3])
            format_string = format_results(columns[:-3], res_tuple)
            #print(len(res), format_string)
            print (self.robot_name, format_string % res_tuple) 
            
    def check_stop(self):
        df_stop   = pd.read_csv('markets_in_trade.txt')

        stop = df_stop[(df_stop['market'] == self.market) & (df_stop['tf'] == self.tf)]['stop']
        if stop.shape[0] == 0: 
            print('В файле markets_in_trade.txt нет установок для данного робота')
            self._running = False
        else:
            self._running = not bool(stop.values[0])

class Robot(TradingSystem):

    def absractloop(self):
        logging.basicConfig(filename='example.log', level=logging.DEBUG)
        logging.info(f"{self.robot.robot_name}, {self.market}, {self.tf}, {self.contract}")
        
        price_buy = 0
        price_sell = 0
        bid, ask = current_bid_ask(exchange, self.symbol)
        ob_price = average_ob_price(bid, ask)

        ob_price_diff = ob_price - self.prev_ob_price
        market_move = np.sign(ob_price_diff)
        self.prev_ob_price = ob_price
        

        self.prices.append(ob_price)
        xx = pd.DataFrame(self.prices, columns = ['C'])
        signals = self.robot.signals(xx)
        signal = signals[-1]
        if signal  == 1 and self.market_position == 0:
            signal = 0    
            price_buy = ask
            price_buy = create_market_buy_order(exchange, self.market, self.contract)
            self.buy(self.contract, price_buy)
        elif signal == -1 and self.market_position == 1:
            signal = 0
            price_sell = bid
            price_sell = create_market_sell_order(exchange, self.market, self.contract) 
            self.sell(price_sell)        
 

        if self.check_stop():
            price_sell = bid
            price_sell = create_market_sell_order(exchange, self.market, self.contract) 
            self.sell(price_sell)

        self.trade_statistics(bid, ask, price_buy, price_sell)
        
   
    def __init__(self, market, tf, robot, contract):
        self.market = market
        self.symbol = market_to_symbol(market)
        self.tf = tf
        self.robot = robot
        self.contract = contract
        self.prev_ob_price = 0
        self.robot_name = f"{self.robot.robot_name}_{market}_{tf}"
        self.stat_fn = self.robot_name + '.csv'
        self.verbose = Verbose.full
        
    def start(self):
        if os.path.exists(self.stat_fn):
            os.remove(self.stat_fn)
        bid, ask = current_bid_ask(exchange, self.symbol)
        self.prev_ob_price = average_ob_price(bid, ask)

        df = pd.DataFrame(exchange.fetch_ohlcv (self.symbol, self.tf))
        df.columns = ['T', 'O', 'H', 'L', 'C', 'V']
        self.prices = df['C'].values.tolist()
        
        df_balance = get_balance()
        balance_cash = get_balance_values(df_balance, 'USDT')
        if balance_cash < self.prices[-1] * self.contract * 1.1:
            print("Not enough cash")
        else:   
            super().__init__(self.market, tf_dict[self.tf])
            
    def set_verbose(self, verbose):
        self.verbose = verbose

#--------------------------Start------------------------------
from TA_robots_01 import rsi, rsi_ma, ma_2_crossover_ichimoku
commission = 0.00075


rk_1 = rsi(11, 36, 73)
r1 = Robot('LINK-USDT', '5m',  rk_1, 10)
r1.start()
r1.set_verbose(Verbose.trades)

time.sleep(1)

rk_2 = rsi_ma(11, 40, 79, 92)
r2 = Robot('LINK-USDT', '1m',  rk_2, 10)
r2.start()
r2.set_verbose(Verbose.trades)

time.sleep(1)

rk_3 = rsi_ma(7, 37, 73, 96)
r3 = Robot('LINK-USDT', '15m',  rk_3, 10)
r3.start()
r3.set_verbose(Verbose.trades)

time.sleep(1)

rk_4 = ma_2_crossover_ichimoku(53, 91)
r4 = Robot('LINK-USDT', '15m',  rk_4, 10)
r4.start()
r4.set_verbose(Verbose.trades)

time.sleep(1)

rk_5 = rsi_ma(4, 38, 74, 109)
r5 = Robot('LINK-USDT', '30m',  rk_5, 10)
r5.start()
r5.set_verbose(Verbose.trades)