import ccxt
import numpy as np
import pandas as pd
import time, ciso8601
from datetime import datetime
import threading
import configparser
from glob import glob
import os
from math import ceil

from tp_config import *

pd.set_option('precision', 9)

def get_symbols(exchange, currency):
    exchange.load_markets()
    symbols = exchange.symbols
    symbols = list(filter(lambda x: currency in x, symbols))
    return symbols


def read_data(market, kline, from_date = '', to_date = ''):
    data_path  = DATA_PATH_CRYPTO
    pair       = market.split('-')[1]
    kline_path = os.path.join(data_path, pair, market, kline)
    files      = glob(kline_path +'/*.csv')
    files.sort()
    ohlcv_file = files[-1]
    
    df = pd.read_csv(ohlcv_file)
    if from_date != '' :
        dt = ciso8601.parse_datetime(from_date)
        from_ts = time.mktime(dt.timetuple()) * 1000
        df = df[df['T'] > from_ts]

    if to_date != '':
        dt = ciso8601.parse_datetime(to_date)
        to_ts = time.mktime(dt.timetuple()) * 1000
        df = df[df['T'] < to_ts]           

    return df

def read_prices(market, kline, from_date = '', to_date = ''):
    df = read_data(market, kline, from_date, to_date)    
    prices = df['C'].values
    return prices

def market_to_symbol(market):
    return market.replace('-','/')

def create_klines(data_path, markets, tf):
    for market in markets:
        print(market)
        pair = market.split('-')[1]
        market_path = data_path + '/' + market
        files = glob(market_path + '/1m/' + '*csv')
        files.sort()
        df = pd.read_csv(files[-1], dtype = {'T':np.str})
        tf_list = []
        tf_blocks = df.shape[0]//tf
        for block in range(tf_blocks):
            start_block = block * tf
            end_block = block * tf + tf - 1
            tf_time = df.iloc[start_block]['T']
            tf_open =  df.iloc[start_block]['O']
            tf_close = df.iloc[end_block]['C']
            tf_high = df.iloc[start_block:end_block+1]['H'].max()
            tf_high = max(tf_open,tf_close, tf_high)
            tf_low = df.iloc[start_block:end_block+1]['L'].min()
            tf_low = min(tf_open, tf_close, tf_low)
            tf_volume = df.iloc[start_block:end_block+1]['V'].sum()
            tf_list.append([tf_time, tf_open, tf_high, tf_low, tf_close, tf_volume])

        tf_df = pd.DataFrame(tf_list, columns = df.columns)
        tf_dir = market_path + '/' + str(tf) + 'm'
        if not os.path.isdir(tf_dir):
            os.makedirs(tf_dir)  

        last_time = tf_df.iloc[-1]['T']
        tf_df.to_csv(tf_dir + '/' + market + '_' + str(last_time) + '.csv', index = False)
        
def cash_data_read(exchange, hold = 30):
    data_path = DATA_PATH_CRYPTO
    cash_data_path = os.path.join(data_path, 'Cash')

    if glob(cash_data_path) == []:
        os.makedirs(cash_data_path)
       
    run = True
    while run:
        now = exchange.milliseconds()
        df = pd.DataFrame({'timestamp':[now], 'time':[exchange.iso8601(now)]})
        file_name = os.path.join(cash_data_path, 'timestamp.csv')
        df.to_csv(file_name, index = False)
        
        df = pd.read_csv("markets_in_trade.csv")
        for row in df.iterrows():
            time.sleep (exchange.rateLimit * 2 / 1000) # time.sleep wants seconds

            market = row[1]['market']
            tf = row[1]['tf']
            symbol = market_to_symbol(market)
            try:
                ohlcvs =  exchange.fetch_ohlcv (symbol, tf)
            except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
                error = exchange.iso8601(now), 'Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...'
                error = ' '.join(error)
                with open(cash_data_path +'/errors.log', 'a') as myfile:
                    myfile.write(error)
                time.sleep(hold)  
            
            
            df = pd.DataFrame(ohlcvs)
            df.columns = ['T', 'O', 'H', 'L', 'C', 'V']
            file_name = os.path.join(cash_data_path, market + '_' + tf + '.csv')
            df.to_csv(file_name, index = False)                  
            
def load_data_from_exchange(exchange, markets, timeframes, start_timestamp, data_path, verbose = True):
        #Обновление данных
    if not os.path.isdir(data_path):
        print("Директория отсутствует")

    if verbose:
        print(start_timestamp, datetime.fromtimestamp(start_timestamp/1000))
    start_time = time.time()

    for market in markets:
        if verbose:
            print(market)
        symbol = market_to_symbol(market)
        folders_exist = next(os.walk(data_path))[1]

        if market not in folders_exist:
            newpath = data_path + '/' + market
            os.makedirs(newpath)

        folders_exist = next(os.walk(data_path + '/' + market))[1]

        tf_keys = list(timeframes.keys())
        for tf in tf_keys:
            if verbose:
                print(tf)
            tf_path = data_path + '/' + market +'/' + tf 
            if tf not in folders_exist:
                os.makedirs(tf_path)

            files = glob(tf_path + '/*.csv')
            from_timestamp = start_timestamp      
            if files != []:
                df_old   = pd.read_csv(files[-1])
                from_timestamp = int(df_old.iloc[-1]['T'])
            else:
                df_old   = pd.DataFrame(columns = ['T', 'O', 'H', 'L', 'C', 'V'])


            data = []        

            time.sleep (exchange.rateLimit / 1000) # time.sleep wants seconds

            try:
                ohlcvs = exchange.fetch_ohlcv (symbol, tf, from_timestamp)  
            except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
                #error_log = exchange.iso8601(now), 'Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...'
                error_log = str(exchange.iso8601(now)), 'Got an error', type(error).__name__, ', retrying in', str(hold), 'seconds...'
                error_log = ' '.join(error_log)
                print(error_log)
                time.sleep(hold)  


            if ohlcvs == []:
                if len(data) > 0:
                    print("Ошибка чтения")
                    from_timestamp = to_timestamp
                    continue
                ohlcvs = exchange.fetch_ohlcv (symbol, tf)
   #             continue

            first  = ohlcvs[0][0]
            last   = ohlcvs[-1][0]
            #print('\t First candle epoch', first, exchange.iso8601(first))
            #print('\t Last candle epoch', last, exchange.iso8601(last), '\n')

            from_timestamp = first  # На случай если на заданную дату данных еще нет
            from_timestamp += len(ohlcvs) * timeframes[tf] * 1000 * 60
            data += ohlcvs
        if data != []:
            df_new = pd.DataFrame(data)
            df_new.columns = ['T', 'O', 'H', 'L', 'C', 'V']
            df = pd.concat([df_old, df_new])
            df = df.drop_duplicates(subset=['T'])
            file_name = tf_path + '/' + market + '_' + str(last) + '.csv'
            df.to_csv(file_name, index = False)  

        files = glob(tf_path + '/*.csv')
        files.sort()
        if len(files) > 1 : 
            os.remove(files[0])

    print('Done')
    time_taken = (time.time() - start_time)/60/60
    print("Time taken = {0:.3f}".format(time_taken),' hours')