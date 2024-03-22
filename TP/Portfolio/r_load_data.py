import numpy as np
import pandas as pd
from datetime import datetime
import os
import ccxt

import sys
sys.path.append("..") 
from tp_config import *
from data_provider import load_data_from_exchange
from portfolio_tools import load_data_for_portfolio

exchange = ccxt.binance()
pair = 'BTC'

timeframes = {'30m':30, '1h':60}

index_assets = pd.read_csv('index_assets.csv')['asset'].tolist()

markets = [s + '-' + pair for s in index_assets]
start_timestamp = exchange.parse8601('2021-05-01 00:00:00')
data_path = DATA_PATH_CRYPTO + '/' + pair

import time
work = True
while work:
    time.sleep(0.9)
    current_time = datetime.now()
    if current_time.minute % 30 != 0:
        continue
        
    print("")        
    print("#----------------------------------------------------------------------#")        
    print("Current time:", "\t", current_time)    
    exchange_now = exchange.milliseconds()/1000
    print("Exchange_time:", "\t",  datetime.fromtimestamp(exchange_now))
    
    ## Load data
    load_data_from_exchange(exchange, markets, timeframes, start_timestamp, data_path, verbose = False)
    for tf in timeframes.items():
        df_prices =  load_data_for_portfolio(markets, tf[0], verbose = False)   
        print('Data_time: ', "\t", datetime.fromtimestamp(df_prices.index[-1]/1000))
    
    time.sleep(60)    