import numpy as np
import pandas as pd
import talib
# signals 0-do nothing, 1-buy, 2-sell


def ma_01(ticks, ma_window):
    ma = talib.MA(ticks, ma_window)
    start = ma_window
    
    robot_log = np.zeros((len(ticks), 3))
    signals = []
    for cur_tick in range(start,len(ticks)):
        price = ticks[cur_tick]
        indicator = ma[cur_tick]
        if market_position == 0 and price > indicator:
            signal = 1
        elif market_position == 1 and price < indicator and bars_since_entry > 0:
            signal = -1
        else:
            signal = 0
            
        bars_since_entry = bars_since_entry + 1
        signals.append(signal)
        #robot_log[cur_tick] = [price, indicator, signal]
    
    
    #np.savetxt('Logs/test.csv', robot_log, delimiter=',')
    return signals
    
def rsi_01 (ticks, window, buy_indicator, sell_indicator):
    indicators_array = talib.RSI(ticks * 100, window)
    start = window
    
    robot_log = np.zeros((len(ticks), 3))
    signals = []
    for cur_tick in range(start,len(ticks)):
        price = ticks[cur_tick]
        indicator = indicators_array[cur_tick]
        if indicator < buy_indicator:
            signal = 1
        elif indicator > sell_indicator:
            signal = -1
        else:
            signal = 0
            
        signals.append(signal)
        #robot_log[cur_tick] = [price, indicator,  signal]
    
    
    #np.savetxt('Logs/test.csv', robot_log, delimiter=',')
    return signals

def ma_crossover_01(ticks, lead_window, lag_window, threshold = 0.018):
    arr = np.zeros((len(ticks), 3))
    arr[:, 0] = ticks
    arr[:, 1] = talib.MA(ticks, lead_window)
    arr[:, 2] = talib.MA(ticks, lag_window)
    ma_df = pd.DataFrame(arr, columns = ['close', 'lead', 'lag'])
    
    ma_df['lead-lag'] = ma_df['lead'] - ma_df['lag']
    ma_df['pc_diff'] = ma_df['lead-lag'] / ma_df['close']
    ma_df['signals'] = np.where(ma_df['pc_diff'] > threshold, 1, 0)
    ma_df['signals'] = np.where(ma_df['pc_diff'] < -threshold, -1, ma_df['signals'])
    
    #ma_df.to_csv('Logs/test.csv', robot_log, delimiter=',')
    
    return ma_df['signals']    

def ma_crossover_ichimoku_01 (ticks, lead_window, lag_window):
    ma_lead = talib.MA(ticks, lead_window)
    ma_lag = talib.MA(ticks, lag_window)
    
    start = lag_window
    signals = np.zeros((len(ticks)))
    for cur_tick in range(start,len(ticks)):
        if ma_lead[cur_tick] > ma_lag[cur_tick] and ma_lag[cur_tick] > ma_lag[cur_tick-1]:
            signals[cur_tick] = 1
        elif ma_lead[cur_tick] < ma_lag[cur_tick] and ma_lag[cur_tick] < ma_lag[cur_tick-1]:
            signals[cur_tick] = -1
     
    #robot_log = np.transpose( np.array([ticks, ma_lead, ma_lag,  signals]))
    #np.savetxt('Logs/test.csv', robot_log, delimiter=',')
    #return robot_log
    return signals

def ma_rsi_01 (ticks, ma_window, rsi_window, sell_indicator):
    rsi = talib.RSI(ticks * 100, rsi_window)
    ma = talib.MA(ticks, ma_window)
    
    start = max(rsi_window, ma_window)
    signals = np.zeros((len(ticks)))
    market_position = 0
    for cur_tick in range(start,len(ticks)):
        if ticks[cur_tick] > ma[cur_tick] and market_position == 0:
            signals[cur_tick] = 1
            market_position = 1
        elif  rsi[cur_tick] > sell_indicator and market_position == 1:
            signals[cur_tick] = -1
            market_position = 0
     
    #robot_log = np.transpose( np.array([ticks, ma, rsi,  signals]))
    #np.savetxt('Logs/test.csv', robot_log, delimiter=',')
    #return robot_log
    return signals