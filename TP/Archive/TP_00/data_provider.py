import ccxt
import numpy as np
import pandas as pd
import time, datetime
import threading
import configparser
from glob import glob
import os
from math import ceil

def get_symbols(exchange, currency):
    exchange.load_markets()
    symbols = exchange.symbols
    symbols = list(filter(lambda x: currency in x, symbols))
    return symbols

def read_data_path():
    config = configparser.ConfigParser()
    config.read("config.ini")
    data_path = config['DEFAULT']['data_path']
    return data_path

def market_to_symbol(market):
    return market.replace('-','/')

def create_klines(data_path, markets, tf):
    for market in markets:
        pair = market.split('-')[1]
        market_path = data_path + '/' + market
        files = glob(market_path + '/1m/' + '*csv')
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
