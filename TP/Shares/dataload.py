import pandas as pd
from pathlib import Path
import shutil
import argparse
import yaml

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.utils import now

import sys
sys.path.append("..")
from tp_config import TINK_DATA
import tink_port as tink


with open('settings.yaml') as f:
    # Load YAML data from the file
    tokens = yaml.load(f, Loader=yaml.FullLoader)
    
class ReadData:
    def __init__(self, Cl, token):
        self.Client = Cl 
        self.token = token
        self.base = []
        self.candles = []
        self.df_port = []

    def read_id_base(self):
        ts = tink.TinkSession(self.Client, self.token)
        base = ts.get_id_base()
        dfx = base[base["type"] == "shares"]
        dfx = dfx[dfx["cur"] == "rub"]
        self.base = dfx.sort_values('ticker')

    def read_candles(self, days: int, verbose: bool = True):
        res = []
        for ind, pos in self.base.iterrows():
            ticker = tink.figi_to_ticker(pos.figi, self.base)
            if verbose:
                print(ticker)
            candles = tink.get_candles(self.Client(self.token),
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
    parser = argparse.ArgumentParser(
                    prog='Download data from Tinkoff',
                    description='Download data from Thinkoff API',
                    epilog='')
    
    parser.add_argument('portfolio', choices=['sandbox', 'momentum']) 
    
    args = parser.parse_args()
    match args.portfolio:
        case 'momentum':
            token = tokens['momentum']
            WorkClient = Client
        case 'sandbox':
            token = tokens['sandbox']
            WorkClient = SandboxClient

    # Тестируем доступность подключения
    with WorkClient(token) as client:
        try:
            client.users.get_info()
            connect = True
        except:
            print("Ошибка подключения! Проверьте токен доступа к API")
            connect = False
            
    if connect:  
        data_reader = ReadData(WorkClient, token)
        data_reader.read_id_base()
        data_reader.read_candles(90)
        data_reader.to_df()
        data_reader.save('portfolio_prices.csv')
    
        date = data_reader.df_port.iloc[-1].name
        print("Last record:", date)
