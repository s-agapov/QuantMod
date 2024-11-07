import numpy as np
import pandas as pd

from datetime import datetime

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import objective_functions

import sys
sys.path.append("..") 
from tp_utils.tp_utils import create_market_sell_order

def print_data(df):
    print(datetime.fromtimestamp(df.index[0]/1000))
    print(datetime.fromtimestamp(df.index[-1]/1000))
    

def weights_to_df(cleaned_weights):
    dfw = pd.DataFrame.from_dict([cleaned_weights]).transpose()
    dfw.columns = ['weights']
    dfw = dfw[dfw['weights'] > 0]
    return dfw

def final_sums(df, total, filt):
    xx = round(df * total, 1)
    return xx[xx['weights'] > filt]


def calc_frontier(df_period, risk_method, ret_method = "mean_historical_return", span = 600, shorts = False):

    if ret_method == "ema_historical_return":
        mu = expected_returns.return_model(df_period, method=ret_method, span = span)
    else:
        mu = expected_returns.return_model(df_period, method=ret_method)
  
    cov_mat = risk_models.risk_matrix(df_period, method=risk_method)        
    if shorts:
        ef = EfficientFrontier(mu, cov_mat,
                               solver = 'ECOS',
                               weight_bounds = (-1, 1))
    else:
        ef = EfficientFrontier(mu, cov_mat,
                               solver = 'ECOS')
    return ef


def calc_weights(ef, opt_type, par, verbose = False):

    if opt_type == 'max_sharpe':
        try:
            weights = ef.max_sharpe()
        except:
            if verbose:
                print("Non-convex optimize!")
            weights = ef.nonconvex_objective(
            objective_functions.sharpe_ratio,
            objective_args=(ef.expected_returns, ef.cov_matrix),
            weights_sum_to_one=True,
        )  
    elif opt_type == 'efficient_risk':
        weights = ef.efficient_risk(par) 

    if verbose:
        print(weights)

    ef.portfolio_performance(verbose=verbose)
    cleaned_weights = ef.clean_weights(cutoff=0.001)
    dfw = weights_to_df(cleaned_weights)
    dfw['weights'] = dfw['weights']/dfw['weights'].sum()
    return dfw

# buy 
def set_new_portfolio(exchange, dfw, balance):
    portfolio = dfw.to_dict()['W']
    overall_balance = balance
    for key in portfolio.keys():
    #    price_buy =  create_market_buy_order(exchange, market, amount)
        ticker = key.replace('-','/')
        price_buy = exchange.fetch_ticker(ticker)['last']
        sum_for_asset = portfolio[key] * overall_balance
        balance = balance - min(sum_for_asset, balance)
        quant = sum_for_asset / price_buy
        portfolio[key] = quant
        if balance < 0:
            print('Balance < 0')    
    return portfolio


def sell_portfolio(exchange, portfolio):
    # Sell portfolio    
    balance = 0.0
    for market in portfolio.keys():
        amount = portfolio[market]
        price_sell = create_market_sell_order(exchange, market, amount) 
    #    ticker = key.replace('-','/')
    #    price_sell = exchange.fetch_ticker(ticker)['last']
        balance = balance + amount * price_sell
    return balance
     
