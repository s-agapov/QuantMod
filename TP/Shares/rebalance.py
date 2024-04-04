import numpy as np
import pandas as pd

import logging
import os
from datetime import timedelta
from pathlib import Path
import argparse
import json

import riskfolio as rp

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now
from tinkoff.invest.caching.market_data_cache.cache import MarketDataCache
from tinkoff.invest.caching.market_data_cache.cache_settings import (
    MarketDataCacheSettings,
)
from tinkoff.invest import OrderDirection, OrderType

import sys
sys.path.append("..") 
from Portfolio.portfolio_tools import *

import tink_port as tink

BASE = 't.UFRJ8SC9hafVOhFxEUY7yf1wZ1gGhwJp-WCp9o4rnEChHWns0c3jQ21eQwoOW_RurFqeZpss2scJkmMQnomJ9g'
MOMENTUM = 't.24WV5_MMG1bQArK1WPp1_DYWD52f-VfGjpR1ci5Pqf0PJ948zWhDstoO_6d4wXIhFTMVsVJSgOzPElUIPEO4Mw'

def riskfolio_weights(df_period, rm , obj):
    """
        obj - Objective function, could be MinRisk, MaxRet, Utility or Sharpe
    """
    Y = df_period.pct_change().dropna()

    # Building the portfolio object
    port = rp.Portfolio(returns=Y)
    port.solvers = ['MOSEK']
    # Calculating optimum portfolio

    # Select method and estimate input parameters:

    method_mu='hist' # Method to estimate expected returns based on historical data.
    method_cov='hist' # Method to estimate covariance matrix based on historical data.

    port.assets_stats(method_mu=method_mu, method_cov=method_cov, d=0.94)

    # Estimate optimal portfolio:

    model='Classic' # Could be Classic (historical), BL (Black Litterman) or FM (Factor Model)
    hist = True # Use historical scenarios for risk measures that depend on scenarios
    rf = 0 # Risk free rate
    l = 0 # Risk aversion factor, only useful when obj is 'Utility'
    # First we need to delete the cardinality constraint
    port.card = None 

    # Then we need to set the constraint on the minimum number of effective assets
    port.nea = 10
    w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)
    w = w[w.weights > 0.01]
    return w

def calculate_portfolio_difference(old_portfolio, new_portfolio):
    """
    Рассчитать разницу между двумя портфелями.

    Args:
        old_portfolio: Словарь, где ключом является тикер, а значением - количество акций.
        new_portfolio: Словарь, где ключом является тикер, а значением - количество акций.

    Returns:
        Словарь, где ключом является тикер, а значением - разница между количеством акций в 
        новых и старых портфелях.
    """

    difference = {}
    for ticker in new_portfolio:
        if ticker in old_portfolio:
            difference[ticker] = new_portfolio[ticker] - old_portfolio[ticker]
        else:
            difference[ticker] = new_portfolio[ticker]

    for ticker in old_portfolio:
        if ticker not in new_portfolio:
            difference[ticker] = -old_portfolio[ticker]
    # Сортировка по значению, по возрастанию
    sorted_diff = sorted(difference.items(), key=lambda x: x[1])

    return sorted_diff

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='Portfolio Rebalance',
                        description='Rebalance Portfolio On Thinkoff API',
                        epilog='')
    
    parser.add_argument('portfolio', choices=['base', 'momentum']) 
    
    args = parser.parse_args()
    if args.portfolio == 'base':
        token = BASE
    elif args.portfolio == 'momentum':
        token = MOMENTUM

    
## ------------------------------------------------        
    accs = tink.get_accounts(token)
    print("Количество аккаунтов:", len(accs.accounts))

    print(accs.accounts[0].name)
    account_id = accs.accounts[0].id    
##--------------------------------------------------
    base = tink.get_id_base(token)
    port = tink.get_portfolio(token)
    df_port = tink.port_to_df(port, base)
##-------------------------------------------------
    print("Скачиваю последние данные")
    dfx = base[base["type"] == "shares"]
    dfx = dfx[dfx["cur"] == "rub"]
    base_ru = dfx.copy()
    
    import time
    res = []
    for ind, pos in base_ru.iterrows():
        time.sleep(1)
        print(pos.figi, pos.ticker)        
        candles = tink.get_candles(token, pos.figi, CandleInterval.CANDLE_INTERVAL_DAY, 30)
        df =  tink.get_open_price(candles)
        ticker = tink.figi_to_ticker(pos.figi, base)

        if ticker == None:
            ticker = pos.figi
        df.columns = [ticker]
        res.append(df)

        df_full = pd.concat(res, axis = 1)
##----------------------------------------------------
    with open('drops.json', 'r') as f:
        drops = json.load(f)
        
    if args.portfolio == 'base':
        dfp = df_full.copy()
        index_assets = pd.read_csv('index_assets.csv')['asset'].values.tolist()
        columns = [x for x in dfp.columns if x in index_assets]

        drops = drops['base']
        columns = [x for x in columns if x not in drops]

        dfp = dfp[columns]
    
    if args.portfolio == 'momentum':
        dfp = df_full.copy()
        drops = drops['momentum']
        columns = [x for x in dfp.columns if x not in drops]
        dfp = dfp[columns]

##-------------------------------------------------------------
    print("Расчет портфеля")
    print()
    
    lookback = 30
    df_period = dfp[-lookback:]

    #print_data(dfp)
    df_period = dfp.dropna(axis = 1)

    dfw = riskfolio_weights(df_period, 'CVaR', 'MaxRet')

##-------------------------------------------------------------
    df_port['sums'] = df_port.quantity * df_port.price
    sum_to_allocate = df_port.sums.sum() - 500
    dfx = final_sums(dfw, sum_to_allocate, 100)
    dfx['lot'] = 1
    inds = dfx.index.values.tolist()

    x = base_ru[base_ru['ticker'].isin (inds)]
    s = x[['ticker', 'lot']].set_index('ticker')
    dfx['lot'] = s
    
    prices = dfp.iloc[-1].T.loc[dfx.index]
    dfx["price"] = prices
    dfx["lot_quantity"] = np.round(dfx.weights/ (dfx.price * dfx.lot)).astype(int)
    dfx["quantity"] =  dfx.lot * dfx.lot_quantity
    dfx["sum"]= dfx.price * dfx.lot_quantity * dfx.lot
    dfx = dfx.sort_values("weights", ascending = False)
    dfx.to_csv("t.csv")
    dfx = dfx.reset_index()
    dfx.columns = ['ticker', 'weights', 'lot', 'price', 'lot_quantity','quantity', 'sums']
    
    def df_to_dict(dfx):
        return {row.ticker:row.lot_quantity for _, row in dfx.iterrows()}

    old_port = df_to_dict(df_port)
    new_port = df_to_dict(dfx)
        
    print("Старый портфель:")
    print(old_port)
    print("Новый портфель:")
    print(new_port)
    
##---------------------------------------------------------------
    print("Корректировка портфеля:")
    rebalance = calculate_portfolio_difference(old_port, new_port)
    for asset, qty in rebalance:
        if asset is None:
            continue

        print(asset, qty)
        
##----------------------------------------
    print("Размещение ордеров")
    

    residuals = []

    with Client(token) as client:

        for asset, qty in rebalance[12:]:
            print(asset)
            if asset is None:
                continue

            figi = tink.ticker_to_figi(asset, base)
            trading_status = client.market_data.get_trading_status(
                figi=figi
            )

            if trading_status.market_order_available_flag and trading_status.api_trade_available_flag:
                if qty < 0:
                    resp = client.orders.post_order(figi=figi,
                                quantity= -qty,
                                direction=OrderDirection.ORDER_DIRECTION_SELL,
                                account_id=account_id,
                                order_type=OrderType.ORDER_TYPE_MARKET,)
                elif qty > 0:
                    resp = client.orders.post_order(figi=figi,
                        quantity=qty,
                        direction=OrderDirection.ORDER_DIRECTION_BUY,
                        account_id=account_id,
                        order_type=OrderType.ORDER_TYPE_MARKET,)
            else:
                print("Не доступно")
                residuals.append((asset, qty))

##----------------------------------------------

    print("Остатки:")

    for asset, qty in residuals:
        if asset is None:
            continue

        print(asset, qty)
        
##--------------------------------
    print("All Done")