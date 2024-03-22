
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
from glob import glob
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt

from keras.layers.core import Dense, Activation, Dropout
from keras.layers import Flatten,  Embedding
from keras.layers.recurrent import LSTM, GRU
from keras.models import Sequential
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger

from sklearn.preprocessing import StandardScaler, Normalizer

from data_provider import read_data_path, read_prices, read_data
from backtest import simulation
np.set_printoptions(edgeitems=30, linewidth=1000, formatter=dict(float=lambda x: "%.7g" % x))


# In[36]:





# In[2]:


pair = 'BTC'
data_path = read_data_path()
data_path = data_path + '/' + pair 
#files = glob(data_path + '/*')
#markets = [x.split('/')[-1] for x in files]
#markets = ['EOS-BTC','TRX-BTC', 'ONT-BTC', 'ZIL-BTC', 'VEN-BTC']
markets = ['BNB-BTC']

timeframes = ['3m', '5m', '15m', '24m', '30m', '1h']
timeframes = ['1h']#['15m' ,'30m ', '1h', '2h', '4h', '6h']


init_data = {'exchange_commission': 0.0005,
             'start_capital'     : 100,
             'buy_correction'    : 1.0001,
             'sell_correction'   : 0.9999,
             'robot_name'        : '',
             'market'            : '',
             'kline'             : ''  
            }


# In[16]:


model = Sequential()
model.add(GRU(input_shape = (None,1), units = 8, dropout = 0.25, recurrent_dropout=0.25, return_sequences=True))
model.add(GRU(input_shape = (None,1), units = 8, dropout = 0.25, recurrent_dropout=0.25, return_sequences=False))
model.add(Dense(1))
model.add(Activation('linear'))
model.compile(loss="mse", optimizer="rmsprop")

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.9, patience=25, min_lr=0.000001, verbose=1)


# In[18]:


res = []
start_time = time.time()

look_back = 100
n_epochs = 5
for market in markets:
    for kline in timeframes:
        prices = read_prices(market, kline)
        #returns = df['C'].pct_change().fillna(0)
        returns = np.diff(np.log(prices))

        timeseries = np.atleast_2d(returns)
        if timeseries.shape[0] == 1:
                timeseries = timeseries.T
        X = np.atleast_3d(np.array([timeseries[start:start + look_back] for start in range(0, timeseries.shape[0] - look_back)]))
        y = np.sign(timeseries[look_back:])
        
        train = int(0.8 * y.shape[0])

        X_train = X[:train]  
        y_train = y[:train]
  
        X_test  = X[train:]
        y_test  = y[train:]
        
        model.fit(X_train, y_train, validation_split=0.33,
          epochs  = n_epochs, batch_size = 32, 
#          callbacks=[reduce_lr],                  
          verbose = 1, shuffle = False)
        
        
        y_pred = model.predict(X_test)
        acc = model.evaluate(X_test, y_test, batch_size = 32)
        print(market, kline, "MSE:", acc)
        
        signals = np.sign(y_pred).flatten()
        bt_prices = prices[-signals.shape[0]-1:-1]
        df = simulation(bt_prices, signals, init_data)
        
        df.to_csv('Logs/res_rnn_' + str(n_epochs) + '_' + market + '_' + kline + '.csv')
print("Time taken = {0:.5f}".format((time.time() - start_time)/60),'min')

