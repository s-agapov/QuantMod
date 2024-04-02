import pandas as pd
from pathlib import Path
from datetime import timedelta


from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now
from tinkoff.invest.caching.market_data_cache.cache import MarketDataCache
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)


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

def port_to_df(port, base):

    res = []
    for pos in port.positions:
        ticker = figi_to_ticker(pos.figi, base)
        name =  figi_to_name(pos.figi, base)
        res.append({
            'figi': pos.figi,
            'ticker': ticker,
            'name': name,
            'quantity' : pos.quantity.units,
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

def get_candles(token, figi, interval, days):
    res = []
    with Client(token) as client:
        settings = MarketDataCacheSettings(base_cache_dir=Path("D:\Data\Tink\market_data_cache"))
        market_data_cache = MarketDataCache(settings=settings, services=client)
        for candle in market_data_cache.get_all_candles(
            figi = figi,
            from_= now() - timedelta(days = days),
            interval= interval,
        ):
            price_row = [candle.open,  candle.high, candle.low, candle.close]
            price_row = [money_value(x) for x in price_row]
            res.append([candle.time] + price_row)    
        return res       
    
def get_open_price(candles):
    res = []
    for row in candles:
        sdate = row[0]
        sdate = sdate.strftime("%Y-%m-%d")
        res.append([sdate] + row[1:2]) 
    df = pd.DataFrame(res, columns = ['date', 'ticker'])
    df = df.set_index('date')
    
    return df