import pandas as pd
import numpy as np
from glob import glob
import time
import asyncio
from datetime import datetime

from lockfile import FileLock
import ccxt
pd.set_option('precision', 9)

#----------------------------------------------------Setup-------------------------------
DEBUG = True

main_key = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"

api_key = main_key
api_secret = main_secret

exchange = ccxt.binance({'apiKey': api_key,
                         'secret': api_secret})
commission = 0.00075

tf_dict = {'1m':60, '3m':180, '5m':300, '15m':1500, '30m': 3000, '1h':6000}
balance_assets = ['USDT','BTC','BNB']
alive_message = 'alive'
lock = FileLock('states.lock')

#------------------------------------Helpers-----------------------------
def market_to_symbol(market):
    return market.replace('-','/')

def exchange_exception(function_to_decorate):
    def wrapper(*args,**kwargs):
        try:
            return function_to_decorate(*args)
        except: #(ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
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

async def main_sleep(delay):
    await asyncio.sleep(delay)

async def save_alive(t, alive_period, robot_name, message):
    """Print a message after the specified delay (in seconds)"""
    freq = int(t/alive_period)
    for i in range(freq):
        await asyncio.sleep(alive_period)

        now = datetime.now()
        mess = message + ' ' + now.strftime('%H:%M:%S')
        file = open(robot_name + '.txt', 'w')
        file.write(mess)
        file.close()


async def sleep_time(t, robot_name):
    # Use asyncio.gather to run two coroutines concurrently:
    await asyncio.gather(
        main_sleep(t),
        save_alive(t, 2, robot_name, alive_message))

#------------------------Trading-------------------------

from threading import Thread
import time
import abc
import logging
import os

import pandas as pd
from collections import namedtuple
Verbose = namedtuple('Verbose', ['mute', 'trades', 'full'])
verbose = Verbose(0, 1, 2)
RobotStates = namedtuple('RobotStates', ['start', 'run', 'stop', 'stop_sell'])
rstates = RobotStates(-1, 0, 1, 2)

alive_message = 'alive'

class TradingSystem(abc.ABC):

    @abc.abstractclassmethod
    def absractloop(self):
        pass

    def mainloop(self):
        print(self.robot_name, self.contract, ', start trading:', datetime.now().strftime('%H:%M:%S'), '\n')
        while(self._running):
            self.absractloop()
            
            if DEBUG :
                asyncio.run(sleep_time(5, self.robot_name))
            else:
                time.sleep(self.timeframe)
        print(self.robot_name, self.contract, 'stop trading:',  datetime.now().strftime('%H:%M:%S'), '\n')


    def __init__(self, market, timeframe):
        self._running = True
        self.timeframe = timeframe
        self.market = market
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
        logs_path = 'Logs/' + self.stat_fn
        if os.path.exists(logs_path):
            df_res = pd.read_csv(logs_path) 
        else:
            df_res = pd.DataFrame(columns = columns) 
        df_res = df_res.append(pd.DataFrame([dict(zip(columns, res))]))
        df_res.to_csv(logs_path, index = False)

        if self.verbose == verbose.full or self.verbose == verbose.trades and (price_sell or price_buy):
            trade_time = datetime.fromtimestamp(res[0]/1000).strftime('%H:%M:%S')
            res_tuple  = tuple([trade_time] + res[1:-3])
            format_string = format_results(columns[:-3], res_tuple)
            print (self.robot_name, format_string % res_tuple) 
            
    def check_stop(self):

            robot_state = pd.read_csv('States/' + self.robot_name + '.txt')

            if robot_state.shape[0] == 0: 
                print('Нет файла установок для данного робота:', self.robot_name)
                self._running = False
            else:
                self.verbose = robot_state['verbose'].values[0]
                contract = robot_state['contract'].values[0]
                if self.market_position == 0:
                    self.contract = contract        

                self._running = (robot_state['state'].values[0] == 0)
        return (robot_state['state'].values[0] == rstates.stop_sell)
    
    def write_states(self):
                robot_state = pd.read_csv('States/' + self.robot_name + '.txt')

                if robot_state.shape[0] == 0: 
                    print('В файле states.txt нет установок для данного робота')
                    self._running = False
                else:

                    df.loc[robot_state, 'MP'] = self.market_position
                    df.loc[robot_state, 'OP'] = self.open_position
                    df.loc[robot_state, 'contract'] = self.contract

                    df.to_csv('states.txt', index = False)
                return

#----------------------------------Robot-------------------------------------------
class Robot(TradingSystem):

    def absractloop(self):
#        logging.basicConfig(filename='example.log', level=logging.DEBUG)
#        logging.info(f"{self.robot.robot_name}, {self.market}, {self.tf}, {self.contract}")
        
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
            if DEBUG:
                price_buy = ask
            else:
                price_buy = create_market_buy_order(exchange, self.market, self.contract)
                
            if price_buy is not None:
                self.buy(self.contract, price_buy)
                signal = 0     
        elif signal == -1 and self.market_position == 1:
            if DEBUG:
                price_sell = bid
            else:
                price_sell = create_market_sell_order(exchange, self.market, self.contract) 
                
            if price_sell is not None:
                self.sell(price_sell)        
                signal = 0 

        if self.check_stop():
            if self.market_position == 1:
                if DEBUG:
                    price_sell = bid
                else:                
                    price_sell = create_market_sell_order(exchange, self.market, self.contract) 
                self.sell(price_sell)
        
        self.write_states()
        self.trade_statistics(bid, ask, price_buy, price_sell)
        
   
    def __init__(self, market, tf, robot, contract):
        self.market = market
        self.tf = tf
        self.robot = robot
        self.contract = contract
        self.prev_ob_price = 0
        self.robot_name = f"{market}_{tf}_{self.robot.robot_name}"
        self.stat_fn = self.robot_name + '.csv'
        self.verbose = verbose.full
        
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
            print(self.robot_name, ', start terminated')
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