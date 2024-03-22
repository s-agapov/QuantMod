#!/usr/bin/env python
# coding: utf-8

# In[4]:


import pandas as pd
import numpy as np
from glob import glob
import time
from datetime import datetime
import csv
import ccxt

from data_provider import market_to_symbol
pd.set_option('precision', 9)

market = 'BTC-USDT'
tf = '1m'
amount = 0.02
commission = 0.00075

main_key = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"


# In[5]:


api_key = main_key
api_secret = main_secret

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


class Robot_02:
    def __init__(self, streak_buy_len, streak_sell_len):
        self.streak_buy = 0
        self.streak_sell = 0
        self.streak_buy_len = streak_buy_len
        self.streak_sell_len = streak_sell_len

    def get_signal(self, te,  market_move):
        if market_move == -1 :
            self.streak_buy += 1
            self.streak_sell = 0
        elif market_move == 1 :
            self.streak_sell +=1
            self.streak_buy = 0

        if te.market_position == 0 and self.streak_buy == self.streak_buy_len:    
            signal = 1
        elif te.market_position == 1 and self.streak_sell == self.streak_sell_len:    
            signal = -1
        else:
            signal = 0
        return signal


# In[ ]:


streak_buy_len = 6
streak_sell_len = 2
alert = -90
stay_away_time = 30
balance_assets = ['USDT','BTC','BNB']

res = []
streak_buy = 0
streak_sell = 0
streak_all = 0
signal = 0
stay_away = 0

te = TradeExec(market, tf, commission)
robot = Robot_02(streak_buy_len, streak_sell_len)

print(te.market, te.tf, contract)
print('Start trading:',  datetime.now())

bid, ask = current_bid_ask(exchange, symbol)
prev_ob_price = average_ob_price(bid, ask)

while not te.stop:
    if stay_away > 0 :
        time.sleep(60)
        stay_away = stay_away - 1
        continue
    else:
        time.sleep(59)
    
    price_buy = 0
    price_sell = 0
    bid, ask = current_bid_ask(exchange, symbol)
    ob_price = average_ob_price(bid, ask)
    
    ob_price_diff = ob_price - prev_ob_price
    market_move = np.sign(ob_price_diff)
    prev_ob_price = ob_price
    
    signal = robot.get_signal(te, market_move)
    
    if ob_price_diff < alert : 
        stay_away = stay_away_time
        signal = -1
       
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
    res.append([trade_time, bid, ask, price_buy, price_sell, market_move, te.market_position, robot.streak_buy, robot.streak_sell, te.num_shares, te.trade_profit, te.cum_profit] + balance)
    
    df = pd.DataFrame(res, columns = ['T', 'bid', 'ask', 'price_buy', 'price_sell', 'move', 'MP', 'streak_buy', 'streak_sell', 'num_shares', 'profit', 'cum_profit'] + balance_assets)
    df.to_csv('test.csv', index = False)
    
    res_tuple = tuple(res[-1][:-3])
    print ('%s bid: %4.2f ask: %4.2f, price_buy: %4.2f, price_sell: %4.2f, move: %2d, MP: %1d, streak_buy: %1d, streak_sell: %1d,  num shares: %1.3f, profit: %4.3f, cum_profit:%4.3f' % res_tuple)     
    #print ('bid:', bid, 'ask:', ask, 'price:', price, 'move:', market_move, 'streak_buy:', streak_buy, 'streak_sell:', streak_sell, 'profit:', trade_profit, 'cum_profit:', cum_profit)    
print('Stop trading:',  datetime.now())
print(te.market, te.tf, contract)


# In[ ]:





# In[ ]:





# In[5]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[86]:





# In[23]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




