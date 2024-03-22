import pandas as pd
import numpy as np
import json
from datetime import datetime
import time
import ccxt


import sys
sys.path.append("..") 
from tp_utils.data_provider import read_data, load_data_from_exchange
from tp_utils.tp_utils import create_market_buy_order,  create_market_sell_order, get_balance
from portfolio_tools import *
from tp_config import *

main_api = "K6oI8dnJvHAbw7UMhRp2dqJ29oLidkR56PZqMpw9yAvNqmu0ZorHlPI8L8KIDHBh"
main_secret = "lOrRq2zRybjZLXX8o7BsA0QOTHeGNLt87mPFje4gPHAPIqyaMCFWMVGNlJXHuikO"


pd.set_option('precision', 9)

#exchange = ccxt.binance({'apiKey': kshao_api, 'secret': kshao_secret})

exchange = ccxt.binance({'apiKey': main_api, 'secret': main_secret})

def sell_portfolio(exchange, portfolio, balance, debug = True):
    df_bal = get_balance(exchange)

    for market in portfolio.keys():
       # print(market)
        asset = market.split('-')[0]
        amount_on_balance = float(df_bal[df_bal['asset'] == asset]['free'].values[0])
        amount_in_portfolio = portfolio[market]

        if debug: 
            amount = amount_in_portfolio
        elif amount_in_portfolio < amount_on_balance:
            amount = amount_in_portfolio
        else:
            amount = amount_on_balance

        if debug:            
            ticker = market.replace('-','/')
            price_sell = exchange.fetch_ticker(ticker)['last']
        else:
            price_sell = create_market_sell_order(exchange, market, amount) 

        balance = balance + amount * price_sell
    return balance
     
def buy_portfolio(exchange, portfolio, balance, debug = True):
    for market in portfolio.keys():
        amount = portfolio[market]
#        print(market, amount)
        if debug:
            ticker = market.replace('-','/')
            price_buy = exchange.fetch_ticker(ticker)['last']
        else:
            price_buy =  create_market_buy_order(exchange, market, amount)
        balance = balance - price_buy * amount
    return balance   

def set_current_portfolio(balance, markets, tf, risk_method, ef_method, par, verbose):
    ## Load data
    df_prices =  load_data_for_portfolio(markets, tf, verbose = False)   
    print('Data time:', datetime.fromtimestamp(df_prices.index[-1]/1000))

    ## set_portfolio
    print('\n', "Set new portfolio")
    df_period = df_prices.iloc[-lookback:]
    ef = calc_frontier(df_period, risk_method,  "ema_historical_return", 250)

    dfw = calc_weights(ef, ef_method, par) 
    portfolio = set_new_portfolio(exchange, dfw, balance)
    print(dfw)
    print(portfolio)
    
    return portfolio, dfw


    
debug = False

pair = 'BTC'
tf = '30m'
tf_len = 30
risk_method =  "semicovariance"
ef_method = "max_sharpe"
ef_par = 0


lookback = 38
horizon = 5
balance = 0.1

r_id = "r_02_" + tf + "_" + lookback + '_' + horizon + '_' + ef_method

timeframes = {tf:tf_len}
index_assets = pd.read_csv('index_assets.csv')['asset'].tolist()

markets = [s + '-' + pair for s in index_assets]
start_timestamp = exchange.parse8601('2021-05-01 00:00:00')
data_path = DATA_PATH_CRYPTO + '/' + pair

portfolio, dfw = set_current_portfolio(balance, markets, tf, risk_method, ef_method, ef_par, verbose = True)
horizon_count = horizon
balance = buy_portfolio(exchange, portfolio, balance, debug = debug)

work = True
d = {"stop": not work}
stop_file = "stop_" + r_id + ".json" 
with open(stop_file, 'w') as f:
    json.dump(d, f)
    
trade_res = []
while work:
    time.sleep(0.9)
    current_time = datetime.now()
    with open(stop_file) as f:
        d = json.load(f)
    if d['stop']:
        balance = sell_portfolio(exchange, portfolio, balance, debug = debug)
        trade = {"time": current_time, "balance":balance, "dfw":dfw, "portfolio":portfolio}
        trade_res.append(trade)
        df_res = pd.DataFrame(trade_res)
        df_res.to_csv("trade_res_" + r_id +".csv", index = False)
        work = False
        print("Stop robot:", current_time)
        continue
        
    if current_time.minute % 30  != 1:
        continue
    else:
        horizon_count = horizon_count - 1
        print(horizon_count)
        if horizon_count != 0:
            time.sleep(60)
            continue
        horizon_count = horizon
        
    time.sleep(10)    
    print("")        
    print("#----------------------------------------------------------------------#")        
    print("Current time:", current_time)    
    
    ##Sell portfolio
    balance = sell_portfolio(exchange, portfolio, balance, debug = debug)

    print('Current balance:', balance)  
    
    portfolio, dfw = set_current_portfolio(balance, markets, tf, risk_method, ef_method, ef_par, verbose = True)

    trade = {"time": current_time, "balance":balance, "dfw":dfw, "portfolio":portfolio}
    trade_res.append(trade)
    df_res = pd.DataFrame(trade_res)
    df_res.to_csv("trade_res_" + r_id +".csv", index = False)
    
    balance = buy_portfolio(exchange, portfolio, balance, debug = debug)
    
    time.sleep(60)