import pandas as pd
import numpy as np

def returns(prices):
    #Functions
    xx = np.diff(np.log(prices))
    xx = np.concatenate([np.zeros(1), xx])
    return xx

def market_to_symbol(market):
    return market.replace('-','/')


def get_balance(exchange):
    json = exchange.fetch_balance({'recvWindow': 59999})
    df = pd.DataFrame(json['info']['balances'])
    return df

def create_market_buy_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_buy_order(symbol, amount)
    trades = exchange.fetchMyTrades (symbol, limit = 1)
    price = trades[-1]['price']
    return price

def create_market_sell_order(exchange, market, amount):
    symbol = market_to_symbol(market)
    order = exchange.create_market_sell_order(symbol, amount)
    trades = exchange.fetchMyTrades (symbol, limit = 1)
    price = trades[-1]['price']
    return price