import numpy as np
import pandas as pd
import talib
# signals 0:do nothing, 1:buy, -1:sell

test = ['ma_2_crossover', 'ma_rsi']
robots = ['ma_2_crossover','ma_2_crossover_ichimoku',  'kestner_ma', 'ma_rsi', 'rsi_ma', 'rsi' ]

#--------------------------Simple moving average -----------------------------
    
class ma_2_crossover:
    robot_name = 'ma-2-crossover'
    ps_names    = ['lead_window', 'lag_window',]
    ps_ranges   = [(5, 80, 2), (20, 160, 2)]
    comment =  ''

    def signals (self, data, lead_window, lag_window):
        ticks = data['C'].values
        ma_lead = talib.MA(ticks, lead_window)
        ma_lag  = talib.MA(ticks, lag_window)
        ma_lead[:lead_window - 1] = 0
        ma_lag[:lag_window - 1]   = 0
        
        start   = lead_window + 1
        signals = np.zeros((len(ticks)))
        signals[ma_lead > ma_lag] =  1
        signals[ma_lead < ma_lag] = -1
        return signals[start:]

class ma_2_crossover_ichimoku: 
    robot_name = 'ma-2-crossover-ichimoku'
    ps_names   = ['ma_lead', 'ma_lag']
    ps_ranges  = [(10, 80, 2), (20, 160, 2)]
    comment =  ''

    def signals (self, data, lead_window, lag_window):
        ticks = data['C'].values
        ma_lead = talib.MA(ticks, lead_window)
        ma_lag  = talib.MA(ticks, lag_window)
        ma_lead[:lead_window - 1] = 0
        ma_lag[:lag_window + 1]   = 0

        signals = np.zeros((len(ticks)))

        ma_lag_shift    = np.roll(ma_lag,1)
        ma_lag_shift[0] = 0

        signals[(ma_lead > ma_lag) & (ma_lag > ma_lag_shift)] =  1
        signals[(ma_lead < ma_lag) & (ma_lag < ma_lag_shift)] = -1
        return signals

class macd:  
    robot_name  = 'macd'
    ps_names    = ['fast_window', 'slow_window', 'signal_window']
    ps_ranges   = ((9,15,1), (20,32,1), (6,12,1))
    comment =  ''
    
    def signals(self, data, fast_window = 12, slow_window = 26, signal_window = 9):
        ticks = data['C'].values
        macd, macd_signal, macd_hist = talib.MACD(ticks, fast_window, slow_window, signal_window)
        start = max(fast_window, slow_window, signal_window)
        macd[np.isnan(macd)] = 0
        macd_signal[np.isnan(macd_signal)] = 0

        signals = np.zeros((len(ticks)))
        signals[(macd > macd_signal) & (macd_signal > 0)]  = 1
        signals[(macd < macd_signal) & (macd_signal < 0)] = -1

        return signals[start:]
#--------------------------------------- Kestner robots -------------------------------    
class kestner_ma:  
    robot_name = 'kestner-ma'
    ps_names    = ['high_window', 'low_window', 'ma_window', 'filt_x']
    ps_ranges   = [(4, 80, 2), (4, 80, 2), (10, 120, 2), (2,30,2) ]
    comment =  'fast trend, 5m'

    def signals (self, data, high_window, low_window, ma_window, filt_x):

        ticks = data['C'].values
        ma_high = talib.MA(data['H'].values, high_window)
        ma_low  = talib.MA(data['L'].values, low_window)
        ma  = talib.MA(ticks, ma_window)

        ma_high[:high_window - 1] = 0
        ma_low[:low_window - 1]   = 0
        ma[:ma_window - 1]        = 0
        ma_shift = np.roll(ma, filt_x)
        ma_shift[:filt_x] = 0


        signals = np.zeros((len(ticks)))
        signals[(ticks > ma_high) & (ma > ma_shift)] = 1 
        signals[(ticks < ma_low) & (ma < ma_shift)]  = -1

        start   = max(high_window,low_window,ma_window +filt_x)
        return signals[start:]
#--------------------------------------- Kestner robots end-------------------------------  
    
    
#--------------------------------------- RSI -------------------------------
class rsi:  
    robot_name  = 'rsi'
    ps_names    = ['rsi_window', 'rsi_buy', 'rsi_sell']
    ps_ranges   = ((4,20,2), (20,40,2), (60,80,2))
    comment =  ''
    
    def signals (self, data, rsi_window, rsi_buy, rsi_sell):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, rsi_window)
        start = rsi_window
        rsi[:start] = 0

        signals = np.zeros((len(ticks)))
        signals[rsi<rsi_buy]  = 1
        signals[rsi>rsi_sell] = -1

        return signals[start:]
    
class rsi_ma:    
    robot_name  = 'rsi_ma'
    ps_names    = ['rsi_window', 'rsi_buy', 'rsi_sell', 'ma_window']
    ps_ranges   = ((4,20,2), (20,40,2), (50,80,2), (80, 120, 2))
    comment =  ''
           
    def signals (self, data, rsi_window, rsi_buy, rsi_sell, ma_window):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, rsi_window)
        ma  = talib.MA(ticks, ma_window)

        start   = max(rsi_window, ma_window)
        ma[:start]  = 0
        rsi[:start] = 0

        signals = np.zeros((len(ticks)))
        signals[(rsi < rsi_buy) & (ticks > ma)] =  1 
        signals[rsi > rsi_sell] = -1
        
        return signals[start:]    
    
class ma_rsi:
    
    robot_name = 'ma-rsi'
    ps_names   = ['ma_window', 'rsi_window', 'rsi_sell']
    ps_ranges   = ((4,80,2), (4,24,2), (60,80,2))
    comment =  ''
    
    def signals (self, data, ma_window, rsi_window, rsi_sell):
        ticks = data['C'].values
        rsi = talib.RSI(ticks * 100, rsi_window)
        ma  = talib.MA(ticks, ma_window)

        start = max(rsi_window, ma_window)
        ma[:start]  = 0
        rsi[:start] = 0

        ma_shift    = np.roll(ma,1)
        ma_shift[0] = 0
        
        signals = np.zeros((len(ticks)))
        signals[(ticks > ma) & (ticks < ma_shift)]  =  1 
        signals[rsi > rsi_sell] = -1

        return signals[start:]    
    
#--------------------------------------- Kestner robots -------------------------------    
class kestner_ma:  
    robot_name = 'kestner_ma'
    ps_names    = ['high_window', 'low_window', 'ma_window', 'filt_x']
    ps_ranges   = [(4, 80, 2), (4, 80, 2), (10, 120, 2), (2,30,2) ]
    comment =  ''
    
    def __init__(self, high_window, low_window, ma_window, filt_x):
        self.high_window = high_window
        self.low_window  = low_window
        self.ma_window   = ma_window
        self.filt_x      = filt_x

    def signals (self, data):

        ticks = data['C'].values
        ma_high = talib.MA(data['H'].values, self.high_window)
        ma_low  = talib.MA(data['L'].values, self.low_window)
        ma  = talib.MA(ticks, self.ma_window)

        ma_high[:self.high_window - 1] = 0
        ma_low[:self.low_window - 1]   = 0
        ma[:self.ma_window - 1]        = 0
        ma_shift = np.roll(ma, self.filt_x)
        ma_shift[:self.filt_x] = 0


        signals = np.zeros((len(ticks)))
        signals[(ticks > ma_high) & (ma > ma_shift)] = 1 
        signals[(ticks < ma_low) & (ma < ma_shift)]  = -1

        start   = max(self.high_window, self.low_window, self.ma_window + self.filt_x)
        return signals[start:]
    
    def func(self, prices):
        ticks = np.array(prices)
        ma_high = talib.MA(ticks, self.high_window)
        ma_low  = talib.MA(ticks, self.low_window)
        ma  = talib.MA(ticks, self.ma_window)
        return ('MA_high', ma_high[-1] , 'MA_low', ma_low[-1], 'MA', ma[-1])

#--------------------------------------- Kestner robots end-------------------------------  
    