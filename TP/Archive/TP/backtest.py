import pandas as pd
import numpy as np

def simulation(ticks, signals, init_data):
    market          = init_data['market']
    commission      = init_data['exchange_commission']
    start_capital   = init_data['start_capital']
    buy_correction  = init_data['buy_correction']
    sell_correction = init_data['sell_correction']
     
    cur_capital  = start_capital 
    num_shares   = 0
    trade_profit = 0
    cum_profit   = 0
    
    market_position = 0
    start = len(ticks) - len(signals) 
    ticks = ticks[start:]
    trade_statistics = []
    #trade_statistics = np.zeros((len(signals),7))
    for i in range(len(signals)) :
        
        if market_position == 0 and signals[i] == 1:
            price = ticks[i] * buy_correction
            num_shares   = cur_capital * (1-commission)/price
            trade_profit = -cur_capital
            cur_capital  = 0
            market_position = 1
            
        elif market_position == 1 and signals[i] == -1:
            price = ticks[i] * sell_correction
            cur_capital  = (num_shares * price)*(1-commission)
            trade_profit = trade_profit + cur_capital
            cum_profit  += trade_profit
            num_shares   = 0
            market_position = 0
        else:
            signals[i] = 0
            
        trade_statistics.append([ticks[i], signals[i], market_position, cur_capital, num_shares, trade_profit, cum_profit])            
        #trade_statistics[i] = [ticks[i], signals[i], market_position, cur_capital, num_shares, trade_profit, cum_profit]

    df = pd.DataFrame(trade_statistics)
    df.columns = ['price', 'signal', 'MP', 'capital', 'num_shares', 'profit', 'cum_profit']
    df = df.astype({'signal':np.int32, 'MP':np.int32})
    return df
    #return 0