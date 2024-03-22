import pandas as pd
import numpy as np
from glob import glob
import time
from datetime import datetime

import ccxt
import ta

from data_provider import market_to_symbol
pd.set_option('precision', 9)
from TA_robots_01 import rsi, rsi_ma

commission = 0.00075

main_key = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"

api_key = main_key
api_secret = main_secret

exchange = ccxt.binance({'apiKey': api_key,
                         'secret': api_secret})

tf_dict = {'1m':60, '3m':180, '5m':300, '15m':1500, '30m': 3000, '1h':6000}
balance_assets = ['USDT','BTC','BNB']

##-------------Helpers-------------------------------
def exchange_exception(function_to_decorate):
    def wrapper(*args,**kwargs):
        try:
            return function_to_decorate(*args)
        except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
            print("Something goes wrong")
            time.sleep(5)  
    return wrapper

@exchange_exception
def get_ohlcv(market, tf):
    symbol = market_to_symbol(market)
    df = pd.DataFrame(exchange.fetch_ohlcv(symbol, tf))
    return df

@exchange_exception
def create_market_buy_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_buy_order(symbol, amount)
    trades = exchange.fetchMyTrades(symbol, limit = 1)
    price = trades[-1]['price']
    return price

@exchange_exception
def create_market_sell_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_sell_order(symbol, amount)
    trades = exchange.fetchMyTrades(symbol, limit = 1)
    price = trades[-1]['price']
    return price

@exchange_exception
def current_bid_ask(exchange, market):
    symbol = market_to_symbol(market)
    orderbook = exchange.fetch_order_book (symbol)
    bid = orderbook['bids'][0][0] if len (orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len (orderbook['asks']) > 0 else None
    return (bid, ask)    


@exchange_exception
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

def average_ob_price(bid, ask):
    return round((bid + ask)/2, 2)

def format_results(col, vals):
    xx = zip(col, vals)
    res = []
    for col, val in xx:
        if type(val) == str:
            fr = '%s'
        elif int(val) - val == 0:
            fr = '%d'
        elif abs(int(val) - val) > 0:
            if abs(val) < 0.001:
                fr = '%1.5f'
            elif abs(val) < 50:
                fr = '%2.3f'
            else:
                fr = '%5.2f'
        res.append(col + ': ' + fr)
    res = ', '.join(res)
    return res
#---------------------------Trading system--------------------------------
from threading import Thread
import time
import abc
import logging
import os

from collections import namedtuple
Verbose = namedtuple('Verbose', ['mute', 'trades', 'full'])

class TradingSystem(abc.ABC):

    @abc.abstractclassmethod
    def absractloop(self):
        pass


    def mainloop(self):
        print(self.robot_name, self.contract, ', start trading:', datetime.now().strftime('%H:%M:%S'), '\n')
        while(self._running):
            self.absractloop()
            
            time.sleep(5)
            #time.sleep(self.timeframe)
        print(self.robot_name, self.contract, 'stop trading:',  datetime.now().strftime('%H:%M:%S'), '\n')

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
        df_res.to_csv('Logs/' + self.stat_fn, index = False)

        if self.verbose == Verbose.full or self.verbose == Verbose.trades and (price_sell or price_buy):
            trade_time = datetime.fromtimestamp(res[0]/1000).strftime('%H:%M:%S')
            res_tuple  = tuple([trade_time] + res[1:-3])
            format_string = format_results(columns[:-3], res_tuple)
            print (self.robot_name, format_string % res_tuple) 
            
    def check_stop(self):
        df_stop   = pd.read_csv('robots.txt')

        stop_rule = (df_stop['market'] == self.market) & (df_stop['tf'] == self.tf) & (df_stop['robot'] == self.robot.robot_name)
        stop = df_stop[stop_rule]['state']
        if stop.shape[0] == 0: 
            print('В файле robots.txt нет установок для данного робота')
            self._running = False
        else:
            self._running = (stop.values[0] == 0)

#----------------------------Robot----------------------------------------------
class Robot(TradingSystem):

    def absractloop(self):
       
        price_buy = 0
        price_sell = 0
        res = current_bid_ask(exchange, self.market)
        if res is None:
            return
        else: 
            bid, ask = res
        ob_price = average_ob_price(bid, ask)

        ob_price_diff = ob_price - self.prev_ob_price
        market_move = np.sign(ob_price_diff)
        self.prev_ob_price = ob_price
        

        self.prices.append(ob_price)
        xx = pd.DataFrame(self.prices, columns = ['C'])
        signals = self.robot.signals(xx)
        signal = signals[-1]
        if signal  == 1 and self.market_position == 0:
            price_buy = ask
     #      price_buy = create_market_buy_order(exchange, market, amount)
            if price_buy != None:
                self.buy(self.contract, price_buy)
                signal = 0     
        elif signal == -1 and self.market_position == 1:
            price_sell = bid
     #       price_sell = create_market_sell_order(exchange, market, amount) 
            if price_sell != None:
                self.sell(price_sell)        
                signal = 0 

        if self.check_stop():
            price_sell = bid
            #price_sell = create_market_sell_order(exchange, market, amount) 
            self.sell(price_sell)

        self.trade_statistics(bid, ask, price_buy, price_sell)
        
   
    def __init__(self, market, tf, robot, contract):
        self.market = market
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
            
        res = current_bid_ask(exchange, self.market)
        if res is None:
            bid, ask = 1, 1
        else: 
            bid, ask = res

        self.prev_ob_price = average_ob_price(bid, ask)

        df = get_ohlcv(self.market, self.tf)
        if df is None:
            print('Binance error ohlcv on start')
            return
        
        df.columns = ['T', 'O', 'H', 'L', 'C', 'V']
        self.prices = df['C'].values.tolist()
        
        df_balance = get_balance()
        if df_balance is None:
            print('Binance error balance on start')
            return

        balance_cash = get_balance_values(df_balance, 'USDT')
        if balance_cash < self.prices[-1] * self.contract * 1.1:
            print("Not enough cash")
        else:   
            super().__init__(self.market, tf_dict[self.tf])
            
    def set_verbose(self, verbose):
        self.verbose = verbose
        
    def __repr__(self):
        return self.robot_name
    
