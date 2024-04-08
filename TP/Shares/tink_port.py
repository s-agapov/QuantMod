import pandas as pd
from pathlib import Path
from datetime import timedelta
from datetime import datetime, timezone
import time

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now
from tinkoff.invest.caching.market_data_cache.cache import MarketDataCache
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)

import sys
sys.path.append("..")
from tp_config import *

class TinkPortfolio:
    def __init__(self, Client, token):
        self.Client = Client
        self.token = token
        
    def get_accounts(self):
        with self.Client(self.token) as cl:
            accounts = cl.users.get_accounts()
        return accounts
        
    def get_portfolio(self):
        accounts = self.get_accounts()
        acc_id = accounts.accounts[0].id
        with self.Client(self.token) as cl:
            port = cl.operations.get_portfolio(account_id=acc_id) 
        return port

def get_accounts(token):
    with Client(token) as cl:
        accounts = cl.users.get_accounts()
    return accounts

def get_portfolio(token):
    accounts = get_accounts(token)
    acc_id = accounts.accounts[0].id
    with Client(token) as cl:
        port = cl.operations.get_portfolio(account_id=acc_id) 
    return port


def get_asset_lot(figi, df):
    dfx = df[df['figi'] == figi]   
 
    if dfx.shape[0] > 0 :
        res = dfx['lot'].iloc[0]      
        return res
    else :
        return 1
    
def port_to_df(port, base):

    res = []
    for pos in port.positions:
        ticker = figi_to_ticker(pos.figi, base)
        name =  figi_to_name(pos.figi, base)
        lot  = get_asset_lot(pos.figi, base)
        res.append({
            'figi': pos.figi,
            'ticker': ticker,
            'name': name,
            'quantity' : pos.quantity.units,
            'lot_quantity' : int(pos.quantity.units/lot),
            'price' : money_value(pos.current_price)
        })

    df_port = pd.DataFrame(res)    
    df_port = df_port.sort_values("ticker")    
    return df_port

def get_id_base(token):
    with Client(token) as cl:
        instruments = cl.instruments
        market_data = cl.market_data
    
        l = []
        for method in ['shares', 'currencies', 'futures', 'bonds', 'etfs']:
            for item in getattr(instruments, method)().instruments:
                l.append({
                    'ticker': item.ticker,
                    'figi': item.figi,
                    'type': method,
                    'name': item.name,
                    'cur' : item.currency,
                    'lot' : item.lot
                })
    
        df = pd.DataFrame(l)
    return df

def ticker_to_figi(ticker, df):
    dfx = df[df['ticker'] == ticker]   
    if dfx.shape[0] > 0 :
        figi = dfx['figi'].iloc[0]
        return figi
    else:
        return None

def figi_to_ticker(figi, df):
        ## Рубли
    if figi == FIGI_RUB:
        return "0-RUB"
    
    dfx = df[df['figi'] == figi]   
 
    if dfx.shape[0] > 0 :
        ticker = dfx['ticker'].iloc[0]      
        return ticker
    else :
        return None

def figi_to_name(figi, df):
    
    dfx = df[df['figi'] == figi]   
 
    if dfx.shape[0] > 0 :
        res = dfx['name'].iloc[0]      
        return res
    else :
        return None
    
    
def money_value(price):
    return price.units + price.nano / 1e9

def get_candles(token, figi, interval, to_date, days):
    res = []
    with Client(token) as client:
        settings = MarketDataCacheSettings(base_cache_dir=Path(TINK_DATA, 'Cache'))
        market_data_cache = MarketDataCache(settings=settings, services=client)
        count = 0
        rerun = True
        while rerun:
            try:
                for candle in market_data_cache.get_all_candles(
                    figi = figi,
                    from_= to_date - timedelta(days = days),
                    to   = to_date,
                    interval= interval,
                ):
                    price_row = [candle.open,  candle.high, candle.low, candle.close]
                    price_row = [money_value(x) for x in price_row]
                    res.append([candle.time] + price_row)    
                rerun = False
            except:
                count = count + 1
                print("Ошибка связи")
                tim.sleep(2)
                if count == 4:
                    rerun = False
            
        return res     
    
def get_price(candles, price:str):    
    assert price in ["open", "high", "low", "close"]
    res = []
    for row in candles:
        sdate = row[0]
        sdate = sdate.strftime("%Y-%m-%d")
        res.append([sdate] + row[1:])
    df_full = pd.DataFrame(res, columns = ['date', 'open', 'high', 'low', 'close'])
    
    df = df_full[['date', price]]
    df.columns =  ['date', 'ticker']
    df = df.set_index('date')

    
    return df
    
def get_open_price(candles):
    res = []
    for row in candles:
        sdate = row[0]
        sdate = sdate.strftime("%Y-%m-%d")
        res.append([sdate] + row[1:2]) 
    df = pd.DataFrame(res, columns = ['date', 'ticker'])
    df = df.set_index('date')
    
    return df

def get_close_price(candles):
    res = []
    for row in candles:
        sdate = row[0]
        sdate = sdate.strftime("%Y-%m-%d")
        res.append([sdate] + row[4:5]) 
    df = pd.DataFrame(res, columns = ['date', 'ticker'])
    df = df.set_index('date')    
    return df

def get_start_of_day(current_datetime):
  """
  Получить timestamp начала дня по datetime текущего момента.

  Args:
      datetime_timestamp: datetime.datetime.

  Returns:
      Datetime начала дня.
  """

  # Получение даты без времени
  start_of_day_datetime = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)


  return start_of_day_datetime
