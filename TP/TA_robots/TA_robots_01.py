import numpy as np
import pandas as pd
import talib
# signals 0:do nothing, 1:buy, -1:sell

test = ['ma_2_crossover', 'ma_rsi']
robots = ['ma_2_crossover','ma_2_crossover_ichimoku',  'kestner_ma', 'ma_rsi', 'rsi_ma', 'rsi' ]

#--------------------------Simple moving average -----------------------------
    
class ma_2_crossover:
    robot_name = 'ma_2_crossover'
    ps_names    = ['lead_window', 'lag_window',]
    ps_ranges   = [(5, 80, 2), (20, 160, 2)]
    comment =  ''
    
    def __init__(self, lead_window, lag_window):
        self.lead_window = lead_window
        self.lag_window = lag_window
        
    def signals (self, data):
        ticks = data['C'].values
        ma_lead = talib.MA(ticks, self.lead_window)
        ma_lag  = talib.MA(ticks, self.lag_window)
        ma_lead[:self.lead_window - 1] = 0
        ma_lag[:self.lag_window - 1]   = 0
        
        start   = self.lag_window + 1
        signals = np.zeros((len(ticks)))
        signals[ma_lead > ma_lag] =  1
        signals[ma_lead < ma_lag] = -1
        return signals[start:]
    
    def func(self, prices):
        ticks = np.array(prices)
        fast  = talib.MA(ticks, self.lead_window)
        slow  = talib.MA(ticks, self.lag_window)
        return ('fast', fast[-1] , 'slow', slow[-1])

class ma_2_crossover_ichimoku: 
    robot_name = 'ma_2_crossover_ichimoku'
    ps_names   = ['ma_lead', 'ma_lag']
    ps_ranges  = [(10, 80, 2), (20, 160, 2)]
    comment =  ''
    
    def __init__(self, lead_window, lag_window):
        self.lead_window = lead_window
        self.lag_window = lag_window

    def signals (self, data):
        ticks = data['C'].values
        ma_lead = talib.MA(ticks, self.lead_window)
        ma_lag  = talib.MA(ticks, self.lag_window)
        ma_lead[:self.lead_window - 1] = 0
        ma_lag[:self.lag_window + 1]   = 0
        
        start   = self.lag_window + 1
        signals = np.zeros((len(ticks)))

        ma_lag_shift    = np.roll(ma_lag,1)
        ma_lag_shift[0] = 0

        signals[(ma_lead > ma_lag) & (ma_lag > ma_lag_shift)] =  1
        signals[(ma_lead < ma_lag) & (ma_lag < ma_lag_shift)] = -1
        return signals[start:]
    
    def func(self, prices):
        ticks = np.array(prices)
        fast  = talib.MA(ticks, self.lead_window)
        slow  = talib.MA(ticks, self.lag_window)
        return ('fast', fast[-1] , 'slow', slow[-1])


    
#--------------------------------------- RSI -------------------------------
class rsi:  
    robot_name  = 'rsi'
    ps_names    = ['rsi_window', 'rsi_buy', 'rsi_sell']
    ps_ranges   = ((4,20,2), (20,40,2), (60,80,2))
    comment =  ''
    def __init__(self, rsi_window, rsi_buy, rsi_sell):
        self.rsi_window = rsi_window
        self.rsi_buy    = rsi_buy
        self.rsi_sell   = rsi_sell
        
    def signals(self, data):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        start = self.rsi_window
        rsi[:start] = 0

        signals = np.zeros((len(ticks)))
        signals[rsi < self.rsi_buy]  = 1
        signals[rsi > self.rsi_sell] = -1

        return signals[start:]
    
    def func(self, prices):
        ticks = np.array(prices)
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        return ('RSI', rsi[-1])
    
class rsi_ma:    
    robot_name  = 'rsi_ma'
    ps_names    = ['rsi_window', 'rsi_buy', 'rsi_sell', 'ma_window']
    ps_ranges   = ((4,20,2), (20,40,2), (50,80,2), (80, 120, 2))
    comment =  ''
    
    def __init__(self, rsi_window, rsi_buy, rsi_sell, ma_window):
        self.rsi_window = rsi_window
        self.ma_window  = ma_window
        self.rsi_buy    = rsi_buy
        self.rsi_sell   = rsi_sell
            
    def signals (self, data):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        ma  = talib.MA(ticks, self.ma_window)

        start   = max(self.rsi_window, self.ma_window)
        ma[:start]  = 0
        rsi[:start] = 0

        signals = np.zeros((len(ticks)))
        signals[(rsi < self.rsi_buy) & (ticks > ma)] =  1 
        signals[rsi > self.rsi_sell] = -1
        
        return signals[start:]    
    
    def func(self, prices):
        ticks = np.array(prices)
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        ma  = talib.MA(ticks, self.ma_window)
        return ('RSI', rsi[-1] , 'MA', ma[-1])

    
class ma_rsi:
    
    robot_name = 'ma_rsi'
    ps_names   = ['ma_window', 'rsi_window', 'rsi_sell']
    ps_ranges   = ((4,80,2), (4,24,2), (60,80,2))
    comment =  ''
    
    def __init__(self, rsi_window,  rsi_sell, ma_window):
        self.rsi_window = rsi_window
        self.ma_window  = ma_window
        self.rsi_sell   = rsi_sell
    
    def signals (self, data):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        ma  = talib.MA(ticks, self.ma_window)

        start = max(self.rsi_window, self.ma_window)
        ma[:start]  = 0
        rsi[:start] = 0

        ma_shift    = np.roll(ma,1)
        ma_shift[0] = 0
        
        signals = np.zeros((len(ticks)))
        signals[(ticks > ma) & (ticks < ma_shift)]  =  1 
        signals[rsi > rsi_sell] = -1

        return signals[start:]    
    
    def func(self, prices):
        ticks = np.array(prices)
        rsi = talib.RSI(ticks * 100, self.rsi_window)
        ma  = talib.MA(ticks, self.ma_window)
        return ('RSI', rsi[-1] , 'MA', ma[-1])
