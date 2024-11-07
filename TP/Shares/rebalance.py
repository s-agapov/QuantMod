import numpy as np
import pandas as pd

import argparse
import json
import yaml

import riskfolio as rp


import sys
sys.path.append("..") 
from Portfolio.portfolio_tools import *
from dataload import ReadData

from tinkoff.invest import  Client
from tinkoff.invest.sandbox.client import SandboxClient
import tink_port as tink


with open('settings.yaml') as f:
    # Load YAML data from the file
    config = yaml.load(f, Loader=yaml.FullLoader)

sandbox_account_id = config["sandbox_account"]

def riskfolio_weights(df_period, rm , obj):
    """
        obj - Objective function, could be MinRisk, MaxRet, Utility or Sharpe
    """
    Y = df_period.pct_change().dropna()

    # Building the portfolio object
    port = rp.Portfolio(returns=Y)
 #   port.solvers = ['MOSEK']
    # Calculating optimum portfolio

    # Select method and estimate input parameters:

    method_mu='hist' # Method to estimate expected returns based on historical data.
    method_cov='hist' # Method to estimate covariance matrix based on historical data.

    port.assets_stats(method_mu=method_mu, method_cov=method_cov)

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
#    sorted_diff = sorted(difference.items(), key=lambda x: x[1])
#    sorted_diff = {k:v for k,v in sorted_diff}
    return difference

def df_to_dict(dfx):
    d = {row.ticker:row.lot_quantity for _,row in dfx.iterrows()}
    return d
    
def sort_dict(d):
    sd = dict(sorted(d.items()))
    return sd
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='Portfolio Rebalance',
                        description='Rebalance Portfolio On Thinkoff API',
                        epilog='')
    
    parser.add_argument('portfolio', choices=['sandbox', 'base', 'momentum']) 
    parser.add_argument('-l','--lookback',  default=30, type=int, help='Lookback period', nargs='?')
    parser.add_argument('-v','--verbose',  default=False, type=bool, help='Print debug info', nargs='?')
    
    args = parser.parse_args()
    if args.portfolio == 'base':
        token = config["base"]
        WorkClient = Client
    elif args.portfolio == 'momentum':
        token = config["momentum"]
        WorkClient = Client
    elif args.portfolio == 'sandbox':
        token = config["sandbox"]
        WorkClient = SandboxClient
    
## ------------------------------------------------        
    ts = tink.TinkSession(WorkClient, token)
    
    accs = ts.get_accounts()
    print("Количество аккаунтов:", len(accs.accounts))

    print(accs.accounts[0].name)
    account_id = accs.accounts[0].id

## ------- Read Tinkoff base
    base = ts.get_id_base()

    dfx = base[base["type"] == "shares"]
    dfx = dfx[dfx["cur"] == "rub"]
    base_ru = dfx.copy()

## ------- Read current portfolio
    port = ts.get_portfolio()
    df_port = tink.port_to_df(port, base)

##---------- Read data from portfolio prices
    reader = ReadData(WorkClient, token)
    df_full = reader.load('portfolio_prices.csv')

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
    elif args.portfolio == 'momentum':
        dfp = df_full.copy()
        drops = drops['momentum']
        columns = [x for x in dfp.columns if x not in drops]
        dfp = dfp[columns]
    elif args.portfolio == 'sandbox':
        dfp = df_full.copy()
        drops = drops['momentum']
        columns = [x for x in dfp.columns if x not in drops]
        dfp = dfp[columns]
    else:
        raise Exception("Unknown portfolio")
        
##-------------------------------------------------------------
    print("Расчет портфеля")
    print()
    
    lookback = args.lookback
    df_period = dfp[-lookback:]

    #print_data(dfp)
    df_period = dfp.dropna(axis = 1)

    dfw = riskfolio_weights(df_period, 'CVaR', 'MaxRet')

    verbose = args.verbose
    if verbose:
        print("Расчитанные веса:")
        print(dfw)
##-------------------------------------------------------------
    # Для учета 0-RUB, рубли, у них price == 0
    df_port["price"]= df_port["price"].replace(to_replace = 0, value = 1,)
    df_port['sums'] = df_port.quantity * df_port.price
    if verbose:
        print(df_port)

    sum_to_allocate = df_port.sums.sum() - 500
    if verbose:
        print("Сумма к распределению", sum_to_allocate)    

    dfx = final_sums(dfw, sum_to_allocate, 100)
    dfx['lot'] = 1
    inds = dfx.index.values.tolist()
    if verbose:
        print("Веса с суммами:")
        print(dfx)
    
    x = base_ru[base_ru['ticker'].isin (inds)]
    dfx['lot'] = x[['ticker', 'lot']].set_index('ticker')
    
    prices = dfp.iloc[-1].T.loc[dfx.index]
    dfx["price"] = prices

    dfx["lot_quantity"] = np.round(dfx.weights/ (dfx.price * dfx.lot)).astype(int)
    dfx["quantity"] =  dfx.lot * dfx.lot_quantity
    dfx["sum"]= dfx.price * dfx.lot_quantity * dfx.lot
    dfx = dfx.sort_values("weights", ascending = False)
    dfx.to_csv("t.csv")
    dfx = dfx.reset_index()
    dfx.columns = ['ticker', 'weights', 'lot', 'price', 'lot_quantity','quantity', 'sums']

##-------------------Распределяем остаток суммы по всему портфелю------------------------
    res_sum = sum_to_allocate - dfx.sums.sum()
    if verbose:
        print(f"Остаток суммы к распределению: {res_sum:f.2}")
    res = []
    for ind, row in dfx.iterrows():
        qty = res_sum / row.price
        lot_qty = np.round(qty / row.lot).astype(int)
        pos_sum = lot_qty * row.lot * row.price
        if res_sum >= pos_sum:
            res.append(lot_qty)
            res_sum = res_sum - pos_sum
        else:
            res.append(0)

    dfx['add_lots'] = res
    dfx.lot_quantity = dfx.lot_quantity + dfx.add_lots
    dfx.quantity = dfx.lot_quantity * dfx.lot
    dfx.sums = dfx.quantity * dfx.price

    print()
    print(f'Cумма старого и нового протфеля: {df_port.sums.sum():g}, {dfx.sums.sum():g}')
##-------------------------------------------
    old_port = df_to_dict(df_port)
    new_port = df_to_dict(dfx)

    print()
    print("Старый портфель:")
    print(sort_dict(old_port))
    print("Новый портфель:")
    print(sort_dict(new_port))
    
##-----------Рассчитываем позиции для корректировки портфеля---------------
    print()
    print("Корректировка портфеля:")
    rebalance = calculate_portfolio_difference(old_port, new_port)
    try:
        rebalance.pop("0-RUB")
    except:
        pass

##-------------------Разделяем на продажу и покупку---------------
##----------  Часть покупки отсортирована по важности позиций
    sd = sorted(rebalance.items(), key=lambda x: x[1])
    sorted_rebalance = {k:v for k,v in sd}
    for asset in sorted_rebalance:
        qty = rebalance[asset]
        if asset is None  :
            continue
        print(asset, qty)
        
    sell_part = {}
    buy_part  = {}
    for asset in rebalance:
        qty = rebalance[asset]
        if asset is None  :
            continue
    
        if qty < 0:
            sell_part[asset] = qty
        elif qty >0:
            buy_part[asset] = qty
    
    with open('rebalance.json', 'w') as f:
        json.dump(rebalance, f)

    with open('rebalance_sell.json', 'w') as f:
        json.dump(sell_part, f)
        
    with open('rebalance_buy.json', 'w') as f:
        json.dump(buy_part, f)

    print()
    print("All Done")
