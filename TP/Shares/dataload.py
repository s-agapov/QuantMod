import pandas as pd
from pathlib import Path
import shutil


from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

import sys
sys.path.append("..")
from tp_config import TINK_DATA
import tink_port as tink

ETF = 't.6nHltT1dYSfrVTIV9zF72fxDlB2sXJbRD6iJNpZXTFAN61rmD7m71xPp9ko12ta1JxA06em4YdN36xicnBmjWg'


class ReadData:
    def __init__(self, token: str):
        self.token = token
        self.base = []
        self.candles = []
        self.df_port = []

    def read_id_base(self):
        base = tink.get_id_base(self.token)
        dfx = base[base["type"] == "shares"]
        dfx = dfx[dfx["cur"] == "rub"]
        self.base = dfx.sort_values('ticker')

    def read_candles(self, days: int, verbose: bool = True):
        res = []
        for ind, pos in self.base.iterrows():
            ticker = tink.figi_to_ticker(pos.figi, self.base)
            print(ticker)
            candles = tink.get_candles(self.token,
                                       pos.figi,
                                       CandleInterval.CANDLE_INTERVAL_DAY,
                                       now(),
                                       days)
            res.append((ticker, candles))
        self.candles = res

    def to_df(self):
        res = []
        for ticker, candles in self.candles:
            df = tink.get_open_price(candles)
            df.columns = [ticker]
            res.append(df)
        self.df_port = pd.concat(res, axis=1)

    def save(self, name):
        datapath = Path(TINK_DATA, 'Cache', name)
        with open(datapath, 'w') as f:
            self.df_port.to_csv(f)

    def load(self, name):
        prices_path = Path(TINK_DATA, 'Cache', name)
        with open(prices_path) as f:
            self.df_port = pd.read_csv(prices_path, index_col='date')
        return self.df_port


if __name__ == "__main__":

    shutil.rmtree(Path(TINK_DATA, 'Cache'))
    data_reader = ReadData(ETF)
    data_reader.read_id_base()
    data_reader.read_candles(90)
    data_reader.to_df()
    data_reader.save('portfolio_prices.csv')

    date = data_reader.df_port.iloc[-1].name
    print("Last record:", date)
