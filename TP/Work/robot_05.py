#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
from glob import glob
import time
from datetime import datetime
import csv
import asyncio

import ccxt
import ta

from data_provider import market_to_symbol
pd.set_option('precision', 9)

market = 'BTC-USDT'
tf = '1h'
amount = 0.02
commission = 0.00075

main_api = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"

kshao_api = "LuvsqHIVmpvQKKGnPQZ4QbPWY6FYPhdldEk81zmoWO6ef4jHYWBa4Dgh0IKEaezZ"
kshao_secret = "kLyVpmF4b74y3KGD57wMJR7SA9cQ0op7SJZR6GfluCuXpEwk1l5KnzCwvsDHfzW2"


api_key = kshao_api
api_secret = kshao_secret

exchange = ccxt.binance({'apiKey': api_key,
                         'secret': api_secret})
symbol = market_to_symbol(market)
contract = amount




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


async def main_sleep(delay):
    await asyncio.sleep(delay)

async def save_alive(t, alive_period, message):
    """Print a message after the specified delay (in seconds)"""
    freq = int(t/alive_period)
    for i in range(freq):
        await asyncio.sleep(alive_period)

        now = datetime.now()
        mess = message + ' ' + now.strftime('%H:%M:%S')
        file = open('alive.txt', 'w')
        file.write(mess)
        file.close()


async def sleep_time(t):
    # Use asyncio.gather to run two coroutines concurrently:
    await asyncio.gather(
        main_sleep(t),
        save_alive(t, 2, alive_message),
    )

class TradeExec():
    def __init__(self, market, tf, commission):
        self.market = market
        self.tf = tf
        self.market_position = 0
        self.num_shares  = 0
        self.open_position = 0
        self.trade_profit = 0
        self.cum_profit = 0
        self.trades = 0
        self.commission = commission
        self.stop = False
        
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
        
    def check_stop(self):
        df_stop   = pd.read_csv('markets_in_trade.txt')

        stop = df_stop[(df_stop['market'] == self.market) & (df_stop['tf'] == self.tf)]['stop']
        if stop.shape[0] == 0: 
            print('В файле markets_in_trade.txt нет установок для данного робота')
            self.stop = True
        else:
            self.stop = bool(stop.values[0])
    def __repr__(self):
        return "market: " + self.market + " tf: " + self.tf



class Robot_cross_ma():
        def __init__(self, lead_win, lag_win):
            self.lead_win = lead_win
            self.lag_win  = lag_win
            
        def get_signal(self, te, price):
            ps = pd.Series(price)
            lead_ma = ta.trend.SMAIndicator(ps, self.lead_win).sma_indicator().values
            lag_ma  = ta.trend.SMAIndicator(ps, self.lag_win).sma_indicator().values
            
            self.fast = lead_ma[-1]
            self.slow = lag_ma[-1]
            
            signal = 0
            if   te.market_position == 0 and self.fast > self.slow:
                signal = 1
            elif te.market_position == 1 and self.fast < self.slow:
                signal = -1
                
            return signal
# In[ ]:

alive_message = market + ' ' + tf 
balance_assets = ['USDT','BTC','BNB']

res = []

te = TradeExec(market, tf, commission)
robot = Robot_cross_ma(12, 25)

print(te.market, te.tf, contract)
print('Start trading:',  datetime.now())

bid, ask = current_bid_ask(exchange, symbol)
prev_ob_price = average_ob_price(bid, ask)

df = pd.DataFrame(exchange.fetch_ohlcv (symbol, tf))
df.columns = ['T', 'O', 'H', 'L', 'C', 'V']
prices = df['C'].values.tolist()
while not te.stop:
    asyncio.run(sleep_time(60*60 - 1))
    price_buy = 0
    price_sell = 0
    bid, ask = current_bid_ask(exchange, symbol)
    ob_price = average_ob_price(bid, ask)
    
    ob_price_diff = ob_price - prev_ob_price
    market_move = np.sign(ob_price_diff)
    prev_ob_price = ob_price
    
    prices.append(ob_price)
    signal = robot.get_signal(te, prices)
          
    if signal  == 1:
        signal = 0    
#       te.buy(contract, ask)
        price_buy = create_market_buy_order(exchange, market, amount)
        te.buy(contract, price_buy)
    elif signal == -1:
        signal = 0
        price_sell = create_market_sell_order(exchange, market, amount) 
#       te.sell(bid)        
        te.sell(price_sell)

#   te.check_stop(bid)
    if te.check_stop():
        price_sell = create_market_sell_order(exchange, market, amount) 
        te.sell(price_sell)
    
    trade_time = exchange.milliseconds()
    df_balance = get_balance()
    balance = get_balance_values(df_balance, balance_assets)
    res.append([trade_time, bid, ask, price_buy, price_sell, te.market_position, robot.fast, robot.slow, te.num_shares, te.trade_profit, te.cum_profit] + balance)
    
    df = pd.DataFrame(res, columns = ['T', 'bid', 'ask', 'price_buy', 'price_sell', 'MP', 'fast', 'slow',  'num_shares', 'profit', 'cum_profit'] + balance_assets)
    df.to_csv('ts_' + market + '_' + tf + '.csv', index = False)

    trade_time = datetime.fromtimestamp(res[-1][0]/1000).strftime('%H:%M:%S')
    res_tuple  = tuple([trade_time] + res[-1][1:-3])
    print ('%s bid: %4.2f ask: %4.2f, price_buy: %4.2f, price_sell: %4.2f,  MP: %1d, fast: %4.2f, slow: %4.2f,  num shares: %1.3f, profit: %4.3f, cum_profit:%4.3f' % res_tuple)     
    
print('Stop trading:',  datetime.now())
print(te.market, te.tf, contract)







